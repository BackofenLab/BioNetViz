<template>
<div id="citation_pane">
    <div id="citation-pane" v-if="active_node !== null">
        <div class="pane_header">
            <a id="abstract-id" href="" v-on:click="google_search(active_node.id)" target="_blank" >PMID: {{active_node.id}}</a>
            <img  class="pane_close" src="@/assets/toolbar/cross.png" v-on:click="close_pane()">
            <img  class="abstract_add" src="@/assets/pathwaybar/plus.png" v-on:click="add_abstract(active_node.id)">
        </div>
        <div class="pane-window">
            <div class="text">
                <div class="gene_attribute">
                    <div class="abstracts_attr"> {{active_node.attributes['Title']}} </div>
                </div>
                <div class="tool-section-active citborder">
                    <div id="informations" class="subsection">
                        <div class="subsection-header abstract-header">
                            <span> year:{{active_node.attributes['Year']}}</span>
                            <span> citations:{{active_node.attributes['Citation']}}</span>
                            <span> deg:{{active_node.attributes['Degree']}};</span>
                            <span> pr:{{Math.abs(Math.log10(active_node.attributes["PageRank"])).toFixed(2)}}</span>
                        </div>
                        <div class="subsection-main abstract">
                            <div id="chatbot">
                                <div class="text">{{active_node.attributes['Abstract']}}</div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</template>

<script>

export default {
    name: 'CitationPane',
    props: ['active_node'],
    emits:['active_node_changed'],
    data() {
        return {
        }
    },
    methods:{
        google_search(id){
            document.getElementById("abstract-id").setAttribute("href","http://www.ncbi.nlm.nih.gov/pubmed/" + id)
        },
        add_abstract(id){
            this.emitter.emit('addNodeToSummary', id)
        },
        close_pane(){
            this.$emit('active_node_changed', null)
        }
    }
}
</script>

<style>
    .abstract {
        background: #0A0A1A;
    }

    #citation-pane .abstract_add {
        right: 9%;
        width: 0.5vw;
        height: 0.5vw;
        position: absolute;
    }

    #citation-pane {
        position: absolute;
        right: 1vw;
        top: 1vw;
        width: 24vw;
        display: block;
        background: #D9D9D9;
        align-items: center;
        z-index: 99;
    }

    .text {
        height: 100%;
    }

    .gene_attribute{
        display: flex;
        font-family: 'ABeeZee', sans-serif;
        align-items: center;
        justify-content: center;
        background: #D9D9D9;
        color:  #0A0A1A;
        padding: 0 0.5vw 0 0.5vw;
    }
    .tool-section{
        height: 0vw;
    }

    .tool-section-active{
        height: 10vw;
    }

    #colorbar {
        position: relative;
        display: flex;
        border-radius: 100%;
        width: 0.5vw;
        height: 0.5vw;
    }
    .gene{
        margin-left: 0.3vw;
        font-size: 0.9vw;
    }
    .abstracts_attr{
        font-size: 0.7vw;
        margin-left: 0.3vw;
        font-weight: bold;
    }

    .nodeattributes{
        position: absolute;
        display: flex;
        width: 100%;
        height: 2vw;
        align-items: center;
        justify-content: center;
    }
    .nodeattributes .icons{
        width: 0.8vw;
        height: 0.8vw;
        margin: 0 0.5vw 0 0.5vw;
    }
    .nodeattributes .subsection {
        margin-bottom: 4%;
        position: relative;
        width: 90%;
    }

    #citation-pane .subsection .subsection-header {
        position: absolute;
        width: 98%;
        display: flex;
        justify-content: left;
        align-items: center;
        font-family: 'ABeeZee', sans-serif;
        font-size: 0.7vw;
        padding: 0.2vw 0 0 0.5vw;
        color: rgba(255,255,255,0.5);
        z-index: 999;
        background-color: #0A0A1A;
    }

    .subsection .abstract-header span{
        padding: 0.5vw;
    }

    #citation-pane .pane_header a {
        height: 100%;
        display: flex;
        font-size: 0.9vw;
        font-family: 'ABeeZee', sans-serif;
        align-items: center;
        text-decoration: none;
    }

    .subsection .subsection-header img{
        position: absolute;
        width: 50%;
        right: -15%;
        display: -webkit-flex;
        padding: 1%;
        padding: 5% 23% 5% 23%;
        filter: invert(100%);

    }

    .subsection .subsection-main {
        height: 100%;
        width: 100%;
        padding-top: 1vw;
    }


    #citation-pane .pane_header{
        color:  #0A0A1A;
        height: 1.5vw;
        width: 100%;
        padding: 0.6vw;
        display: flex;
        align-items: center;
        justify-content: center;
        border-bottom: 0.05vw solid #0A0A1A;
    }
    #citation-pane .pane_header span{
        height: 100%;
        display: flex;
        font-size: 0.9vw;
        font-family: 'ABeeZee', sans-serif;
        align-items: center;
    }

    #citation-pane .pane_close{
        right: 3%;
        width: 0.5vw;
        height: 0.5vw;
        position: absolute;
    }

    .citborder{
        border: #D9D9D9;;
        border-width: 0.2px;
        border-style: solid;
    }

    #citation-pane #chatbot{
        padding: 1vw 1.3vw 1vw 1.3vw;
    }

</style>