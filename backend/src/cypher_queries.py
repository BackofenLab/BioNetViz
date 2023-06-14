"""
Collection of Cypher queries for writing and reading the resulting
Neo4j graph database.
"""

import uuid
import subprocess

TERM_FILE = uuid.uuid4()
def get_protein_list(graph):
    """
    Retrieve a list of proteins including the protein ID
    and the protein name.
    """

    query = """
        MATCH (protein:Protein)
        RETURN protein.external_id AS id,
               protein.name AS name,
               protein.species_id AS species_id
    """

    return graph.run(query)
def get_num_proteins():
    """Use Cypher query call to get the total number of proteins
    Args:
        Right now none, default organism is mus musculus
        When more organism databases are implemented,
        add species_id to clarify from which organism
    Return:
        Number of proteins(int)
    """

    data = subprocess.run(
        [
            "cypher-shell",
            "-a",
            "bolt://localhost:7687",
            "-u",
            "neo4j",
            "-p",
            "pgdb",
            "MATCH (n:Protein) RETURN count(n)",
        ],
        capture_output=True,
        encoding="utf-8",
    )

    # Check standard output 'stdout' whether it's empty to control errors
    if not data.stdout:
        raise Exception(data.stderr)

    # all proteins of organism: background proteins
    num_proteins = int(data.stdout[9:])
    return num_proteins


# number of proteins in the whole organism
NUM_PROTEINS = get_num_proteins()


def create_term_df():
    """Use Cypher query to create a dataframe with all terms and their
    properties from the database
    Args:
        Right now none, default organism is mus musculus
        When more organism databases are implemented,
        add species_id to clarify from which organism
    """

    query = (
        """
                WITH "MATCH (term:Terms)
                RETURN term.external_id AS id, term.name AS name, term.category AS category, term.proteins AS proteins"
                AS query
                CALL apoc.export.csv.query(query, "/tmp/"""
        + repr(TERM_FILE)
        + """.csv", {})
                YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
                RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data;
                """
    )

    with open("/tmp/query" + repr(TERM_FILE) + ".txt", "w") as query_text:
        query_text.write("%s" % query)

    # Run the cypher query in cypher shell via terminal
    data = subprocess.run(
        [
            "cypher-shell",
            "-a",
            "bolt://localhost:7687",
            "-u",
            "neo4j",
            "-p",
            "pgdb",
            "-f",
            "/tmp/query" + repr(TERM_FILE) + ".txt",
        ],
        capture_output=True,
        encoding="utf-8",
    )
    # Check standard output 'stdout' whether it's empty to control errors
    if not data.stdout:
        raise Exception(data.stderr)
