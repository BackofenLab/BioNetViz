import pandas as pd
import utils
import main


def create_study_cell_source_meancount():
    print("Creating Study, Celltype, Source and MeanCount nodes ...")
    study_info_str = (
        "{" + ", ".join(["{}: '{}'".format(c, main._DEFAULT_STUDY_INFO[c]) for c in main._DEFAULT_STUDY_INFO]) + "}"
    )
    celltype_info_str = (
        "{"
        + ", ".join(["{}: '{}'".format(c, main._DEFAULT_CELLTYPE_INFO[c]) for c in main._DEFAULT_CELLTYPE_INFO])
        + "}"
    )

    create_study_query = "MERGE (s:Study {})".format(study_info_str)
    create_celltype_query = "MERGE (c:Celltype {})".format(celltype_info_str)
    create_source_query = "MERGE (s)-[:HAS]->(o:Source)<-[:HAS]-(c) SET o.id = id(o)"
    create_meancount = "MERGE (m:MeanCount)"
    create_source_meancount_edge = "MERGE (o)-[:HAS]->(m)"
    return_id = "RETURN id(o) AS id"

    query = (
        create_study_query
        + " "
        + create_celltype_query
        + " "
        + create_source_query
        + " "
        + create_meancount
        + " "
        + create_source_meancount_edge
        + " "
        + return_id
    )
    result, _, _ = utils.execute_query(query=query, read=False)

    return result[0]["id"]


def create_nodes(source_file: str, type_: str, id: str, reformat_values: list[tuple[str]]):
    """
    Common function to create nodes in the Neo4j Database (MERGE not CREATE)

    Variables:
        source_file -> Name of file in neo4j import directory
        type_ -> Type of node (e.g. TG, Context, ...)
        id -> Identifier of node (TG / TF is ENSEMBL, OR is nearest_index)
        reformat_values -> List of Tuples, where 0 -> Name of Value, 1 -> Function to reformat
    """

    id_str = "{" + "{}: map.{}".format(id, id) + "}"
    load_data_query = "LOAD CSV WITH HEADERS from 'file:///{}' AS map RETURN map".format(source_file)
    merge_into_db_query = "MERGE (t:{} {} ) SET t = map".format(type_, id_str)
    reformat_values_str = " ".join(["SET t.{} = {}(t.{})".format(v[0], v[1], v[0]) for v in reformat_values])

    # For large numbers of nodes, using apoc.periodic.iterate
    # For info, see: https://neo4j.com/labs/apoc/4.2/overview/apoc.periodic/apoc.periodic.iterate/

    per_iter = 'CALL apoc.periodic.iterate("{}", "{}", {{batchSize: 1000, parallel: true}} )'.format(
        load_data_query, merge_into_db_query + " " + reformat_values_str
    )

    utils.execute_query(query=per_iter, read=False)
    return


def create_relationship(
    source_file: str,
    type_: str,
    between: tuple[str],
    node_types: tuple[str],
    values: list[str],
    reformat_values: list[tuple[str]],
    merge: bool = False,
):
    """
    Common function to create edges in Neo4j Database (both MERGE and CREATE possible, see merge flag)

    Variables:
        source_file -> Name of file in neo4j import directory
        type_ -> Type of relationship (e.g. HAS, DE, ...)
        between -> Comparing value names (0 -> Origin of relationship, 1 -> Destination of relationship; x.0 -> Value in DB, x.1 Value in CSV
        node_types -> Nodetypes (0 -> Origin of relationship, 1 -> Destination of relationship)
        values -> Column names in csv that need to be added as properties
        reformat_values -> List of Tuples, where 0 -> Name of Value, 1 -> Function to reformat
        merge -> Use CREATE or MERGE
    """

    # TODO: Try trick of generating nodes first, then relationships; Generating edges is very slow...
    comparing_reformat_values = [v[0] for v in reformat_values]
    m_query = (
        "m.{} = {}map.{}{}".format(
            between[0][0],
            ""
            if between[0][1] not in comparing_reformat_values
            else reformat_values[comparing_reformat_values.index(between[0][1])][1] + "(",
            between[0][1],
            "" if between[0][1] not in comparing_reformat_values else ")",
        )
        if len(between[0]) == 2
        else ""
    )
    n_query = (
        "n.{} = {}map.{}{}".format(
            between[1][0],
            ""
            if between[1][1] not in comparing_reformat_values
            else reformat_values[comparing_reformat_values.index(between[1][1])][1] + "(",
            between[1][1],
            "" if between[1][1] not in comparing_reformat_values else ")",
        )
        if len(between[1]) == 2
        else ""
    )
    load_data_query = (
        "LOAD CSV WITH HEADERS from 'file:///{}' AS map MATCH (m:{}), (n:{}) WHERE{}{}{}RETURN map, n, m".format(
            source_file,
            node_types[0],
            node_types[1],
            " " + n_query + " ",
            "AND" if n_query != "" and m_query != "" else "",
            " " + m_query + " ",
        )
    )
    comparing_reformat_values = [v[0] for v in reformat_values]
    set_values_query = " ".join(
        [""] + ["SET e.{} = map.{}".format(v, v) for v in values if v not in comparing_reformat_values]
    )
    set_values_query += " ".join(
        [""] + ["SET e.{} = {}(map.{})".format(v[0], v[1], v[0]) for v in reformat_values if v[0] in values]
    )

    if merge:
        create_edge_query = "MERGE (m)-[e:{}]->(n)".format(type_) + set_values_query
    else:
        create_edge_query = "CREATE (m)-[e:{}]->(n)".format(type_) + set_values_query

    per_iter = 'CALL apoc.periodic.iterate("{}", "{}", {{batchSize: 1000, parallel: true}} )'.format(
        load_data_query, create_edge_query
    )

    utils.execute_query(per_iter, read=False)
    return


def create_tg_nodes(nodes: pd.DataFrame, source: int):
    print("Creating Target Gene nodes ...")

    # filter for MeanCount values to add later
    mean_count = nodes.filter(items=["ENSEMBL", "mean_count"])
    mean_count["Source"] = source
    mean_count = mean_count.rename(columns={"mean_count": "Value"})

    # create new Target Gene nodes for every new TG
    nodes = nodes.drop(columns=["mean_count"])
    utils.save_df_to_csv(file_name="tg.csv", df=nodes, override_prod=True)
    create_nodes(source_file="tg.csv", type_="TG", id="ENSEMBL", reformat_values=[("ENTREZID", "toInteger")])

    print("Creating MEANCOUNT edges for Target Genes ...")

    # create MeanCount edges for TGs
    utils.save_df_to_csv(file_name="tg_meancount.csv", df=mean_count)
    create_relationship(
        source_file="tg_meancount.csv",
        type_="MEANCOUNT",
        between=((), ("ENSEMBL", "ENSEMBL")),
        node_types=("MeanCount", "TG"),
        values=["Value", "Source"],
        reformat_values=[("Value", "toFloat"), ("Source", "toInteger")],
    )


def create_tf_nodes(nodes: pd.DataFrame, source: int):
    print("Creating Transcription Factor nodes ...")

    # filter for MeanCount values to add later
    mean_count = nodes.filter(items=["ENSEMBL", "mean_count"])
    mean_count["Source"] = source
    mean_count = mean_count.rename(columns={"mean_count": "Value"})

    # create new Transcription Factor node for every new TF
    nodes = nodes.drop(columns=["mean_count"])
    utils.save_df_to_csv(file_name="tf.csv", df=nodes, override_prod=True)
    create_nodes(source_file="tf.csv", type_="TF:TG", id="ENSEMBL", reformat_values=[("ENTREZID", "toInteger")])

    print("Creating MEANCOUNT edges for Transcription Factors ...")

    # create MeanCount edges for TFs
    utils.save_df_to_csv(file_name="tf_meancount.csv", df=mean_count)
    create_relationship(
        source_file="tf_meancount.csv",
        type_="MEANCOUNT",
        between=((), ("ENSEMBL", "ENSEMBL")),
        node_types=("MeanCount", "TF"),
        values=["Value", "Source"],
        reformat_values=[("Value", "toFloat"), ("Source", "toInteger")],
    )


def create_or_nodes(nodes: pd.DataFrame, source: int):
    print("Creating Open Region nodes ...")

    # filter for MeanCount values to add later
    mean_count = nodes.filter(items=["nearest_index", "mean_count"])
    mean_count["Source"] = source
    mean_count = mean_count.rename(columns={"mean_count": "Value"})

    # create new Open Region node for every new OR
    nodes = nodes.drop(columns=["mean_count", "nearest_ENSEMBL"])
    utils.save_df_to_csv(file_name="or.csv", df=nodes, override_prod=True)
    create_nodes(source_file="or.csv", type_="OR", id="nearest_index", reformat_values=[("summit", "toInteger")])

    print("Creating MEANCOUNT edges for Open Regions ...")

    # create MeanCount edges for ORs
    utils.save_df_to_csv(file_name="or_meancount.csv", df=mean_count)
    create_relationship(
        source_file="or_meancount.csv",
        type_="MEANCOUNT",
        between=((), ("nearest_index", "nearest_index")),
        node_types=("MeanCount", "OR"),
        values=["Value", "Source"],
        reformat_values=[("Value", "toFloat"), ("Source", "toInteger")],
    )


def create_context(context: pd.DataFrame, source: int, value_type: int):  # value_type: 1 -> DE, 0 -> DA
    print("Creating Context nodes ...")

    # create Context node for every new context
    nodes = context["Context"].unique()
    node_df = pd.DataFrame.from_records(data=[{"Context": c} for c in nodes])

    utils.save_df_to_csv(file_name="context.csv", df=node_df, override_prod=True)
    create_nodes(source_file="context.csv", type_="Context", id="Context", reformat_values=[])

    print("Connecting Source and Context nodes ...")

    # create HAS edge from source to Context node for every context represented in the source
    source_edge_df = node_df
    source_edge_df["Source"] = source

    # TODO: All context -> other rel not yet working !!!
    utils.save_df_to_csv(file_name="source_context.csv", df=source_edge_df, override_prod=True)
    create_relationship(
        source_file="source_context.csv",
        type_="HAS",
        between=(("id", "Source"), ("Context", "Context")),
        node_types=("Source", "Context"),
        values=[],
        reformat_values=[("Source", "toInteger")],
        merge=True,
    )

    print("Creating Context {} edges ...".format("DE" if value_type == 1 else "DA"))

    # Create DE/DA edges with Values and Source node id
    edge_df = context
    edge_df["Source"] = source

    # DE Edges
    if value_type == 1:
        utils.save_df_to_csv(file_name="de.csv", df=edge_df)
        create_relationship(
            source_file="de.csv",
            type_="DE",
            between=(("Context", "Context"), ("ENSEMBL", "ENSEMBL")),
            node_types=("Context", "TG"),
            values=["Value", "p", "Source"],
            reformat_values=[("Value", "toFloat"), ("Source", "toInteger"), ("p", "toFloat")],
        )

    # DA Edges
    elif value_type == 0:
        utils.save_df_to_csv(file_name="da.csv", df=edge_df)
        create_relationship(
            source_file="da.csv",
            type_="DA",
            between=(("Context", "Context"), ("nearest_index", "nearest_index")),
            node_types=("Context", "OR"),
            values=["Value", "p", "Source"],
            reformat_values=[("Value", "toFloat"), ("Source", "toInteger"), ("p", "toFloat")],
        )


def create_correlation(correlation: pd.DataFrame, source: int, value_type: int):  # value_type: 1 -> TF-TG, 0 -> TG-OR
    print("Creating {} CORRELATION edges ...".format("TF->TG" if value_type == 1 else "OR->TG"))
    correlation["Source"] = source

    # TF-TG edges
    if value_type == 1:
        utils.save_df_to_csv(file_name="tf_tg_corr.csv", df=correlation)
        create_relationship(
            source_file="tf_tg_corr.csv",
            type_="CORRELATION",
            between=(("SYMBOL", "TF"), ("ENSEMBL", "ENSEMBL")),
            node_types=("TF", "TG"),
            values=["Correlation", "Source"],
            reformat_values=[("Correlation", "toFloat"), ("Source", "toInteger")],
        )

    # OR-TG edges
    elif value_type == 0:
        utils.save_df_to_csv(file_name="or_tg_corr.csv", df=correlation)
        create_relationship(
            source_file="or_tg_corr.csv",
            type_="CORRELATION",
            between=(("nearest_index", "nearest_index"), ("ENSEMBL", "ENSEMBL")),
            node_types=("OR", "TG"),
            values=["Correlation", "Source"],
            reformat_values=[("Correlation", "toFloat"), ("Source", "toInteger")],
        )


def create_motif_edges(motif: pd.DataFrame):
    print("Creating MOTIF edges ...")

    utils.save_df_to_csv(file_name="motif.csv", df=motif)
    create_relationship(
        source_file="motif.csv",
        type_="MOTIF",
        between=(("SYMBOL", "TF"), ("nearest_index", "peaks")),
        node_types=("TF", "OR"),
        values=["Motif"],
        reformat_values=[],
        merge=True,
    )


def create_distance_edges(distance: pd.DataFrame):
    print("Creating DISTANCE edges ...")

    utils.save_df_to_csv(file_name="distance.csv", df=distance)
    create_relationship(
        source_file="distance.csv",
        type_="DISTANCE",
        between=(("nearest_index", "nearest_index"), ("ENSEMBL", "nearest_ENSEMBL")),
        node_types=("OR", "TG"),
        values=["Distance"],
        reformat_values=[("Distance", "toInteger")],
        merge=True,
    )


def create_string_edges(gene_gene_scores: pd.DataFrame):
    print("Creating STRING ASSOCIATION edges ...")

    utils.save_df_to_csv(file_name="string_scores.csv", df=gene_gene_scores)
    create_relationship(
        source_file="string_scores.csv",
        type_="STRING",
        between=(("ENSEMBL", "ENSEMBL1"), ("ENSEMBL", "ENSEMBL2")),
        node_types=("TG", "TG"),
        values=["Score"],
        reformat_values=[("Score", "toInteger")],
    )

    return


def create_functional(ft_nodes: pd.DataFrame, ft_ft_overlap: pd.DataFrame, ft_gene: pd.DataFrame):
    print("Creating Functional Term nodes ...")

    utils.save_df_to_csv(file_name="ft_nodes.csv", df=ft_nodes)
    create_nodes(
        source_file="ft_nodes.csv",
        type_="FT",
        id="Term",
        reformat_values=[],
    )

    print("Creating OVERLAP edges ...")
    
    utils.save_df_to_csv(file_name="ft_overlap.csv", df=ft_ft_overlap)
    create_relationship(
        source_file="ft_overlap.csv",
        type_="OVERLAP",
        between=(("Term", "source"), ("Term", "target")),
        node_types=("FT", "FT"),
        values=["Score"],
        reformat_values=[("Score", "toFloat")],
    )

    print("Creating LINK (Gene -> Functional Term) edges ...")

    utils.save_df_to_csv(file_name="ft_gene.csv", df=ft_gene)
    create_relationship(
        source_file="ft_gene.csv",
        type_="LINK",
        between=(("ENSEMBL", "ENSEMBL"), ("Term", "Term")),
        node_types=("TG", "FT"),
        values=[],
        reformat_values=[],
    )
    return


def extend_db_from_experiment(
    tg_nodes: pd.DataFrame,
    tf_nodes: pd.DataFrame,
    or_nodes: pd.DataFrame,
    de_values: pd.DataFrame,
    da_values: pd.DataFrame,
    tf_tg_corr: pd.DataFrame,
    tg_or_corr: pd.DataFrame,
    motif: pd.DataFrame,
    distance: pd.DataFrame,
):
    id_source = create_study_cell_source_meancount()
    create_tg_nodes(nodes=tg_nodes, source=id_source)
    create_tf_nodes(nodes=tf_nodes, source=id_source)
    create_or_nodes(nodes=or_nodes, source=id_source)

    create_context(context=de_values, source=id_source, value_type=1)
    create_context(context=da_values, source=id_source, value_type=0)

    create_correlation(correlation=tf_tg_corr, source=id_source, value_type=1)
    create_correlation(correlation=tg_or_corr, source=id_source, value_type=0)

    create_motif_edges(motif=motif)
    create_distance_edges(distance=distance)

    print("Done extending DB from Experimental Data")
    return


def setup_db_external_info(
    ft_nodes: pd.DataFrame, ft_ft_overlap: pd.DataFrame, ft_gene: pd.DataFrame, gene_gene_scores: pd.DataFrame
):
    create_string_edges(gene_gene_scores=gene_gene_scores)
    create_functional(ft_nodes=ft_nodes, ft_ft_overlap=ft_ft_overlap, ft_gene=ft_gene)

    return


def first_setup(
    tg_nodes: pd.DataFrame,
    tf_nodes: pd.DataFrame,
    or_nodes: pd.DataFrame,
    de_values: pd.DataFrame,
    da_values: pd.DataFrame,
    tf_tg_corr: pd.DataFrame,
    tg_or_corr: pd.DataFrame,
    motif: pd.DataFrame,
    distance: pd.DataFrame,
    ft_nodes: pd.DataFrame,
    ft_ft_overlap: pd.DataFrame,
    ft_gene: pd.DataFrame,
    gene_gene_scores: pd.DataFrame,
):
    # extend_db_from_experiment(
    #     tg_nodes=tg_nodes,
    #     tf_nodes=tf_nodes,
    #     or_nodes=or_nodes,
    #     de_values=de_values,
    #     da_values=da_values,
    #     tf_tg_corr=tf_tg_corr,
    #     tg_or_corr=tg_or_corr,
    #     motif=motif,
    #     distance=distance,
    # )

    setup_db_external_info(
        ft_nodes=ft_nodes,
        ft_ft_overlap=ft_ft_overlap,
        ft_gene=ft_gene,
        gene_gene_scores=gene_gene_scores,
    )
