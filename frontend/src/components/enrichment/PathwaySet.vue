<template>
  <div id="pathways-set">
    <div class="tool-set-section-graph">
      <div class="coloumn-set-button">
        <button class="tool-buttons" v-on:click="apply_enrichment()">
          <img
            class="buttons-img"
            src="@/assets/plus-1.png"
            v-if="!loading_state"
          />
          <div v-if="loading_state" class="loading_button"></div>
        </button>
      </div>
      <div class="citation-search">
        <img class="citation-search-icon" src="@/assets/toolbar/search.png" />
        <input
          type="text"
          v-model="search_raw"
          class="empty"
          placeholder="search in sets"
        />
      </div>
    </div>
    <div class="pathway-apply-section">
      <div class="sorting">
        <a class="enrichment_filter">generated term sets </a>
      </div>

      <div
        class="results"
        tabindex="0"
        @keydown="handleKeyDown"
        ref="resultsContainer"
      >
        <table>
          <tbody>
            <span v-for="(entry, index) in filt_abstracts" :key="index">
              <tr class="set-table">
                <td>
                  <div class="favourite-symbol" v-on:click="set_active(entry)">
                    <label class="custom-checkbox">
                      <div
                        class="active-image"
                        :class="{ checked: entry.status }"
                      ></div>
                    </label>
                  </div>
                </td>
                <td>
                  <div class="pathway-text">
                    <input type="text" v-model="entry.name" class="empty" />
                    <span>({{ entry.terms.length }})</span>
                  </div>
                </td>
                <td>
                  <label class="custom-icons">
                    <div
                      class="expand-image"
                      v-on:click="entry.information = !entry.information"
                    ></div>
                  </label>
                  <label class="custom-icons">
                    <div
                      class="delete-image"
                      v-on:click="remove_set(entry)"
                    ></div>
                  </label>
                </td>
              </tr>
              <tr v-if="entry.information" class="expanded">
                <td v-for="element in entry.stats" :key="element">
                  <div class="information-set">{{ element }}</div>
                </td>
              </tr>
            </span>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "PathwaySet",
  props: ["gephi_data", "api"],
  emits: ["term_set_changed"],
  data() {
    return {
      set_dict: new Set(),
      search_raw: "",
      layer: 0,
      loading_state: false,
    };
  },
  computed: {
    regex() {
      var com = this;
      return RegExp(
        com.search_raw.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
      );
    },
    filt_abstracts() {
      var com = this;
      var filtered = [...this.set_dict];

      if (com.search_raw !== "") {
        // If search term is not empty, filter by search term
        var regex = new RegExp(com.regex, "i");
        filtered = filtered.filter(function (set) {
          return regex.test(set.stats.join(" "));
        });
      }

      return new Set(filtered);
    },
  },
  methods: {
    apply_enrichment() {
      var com = this;
      var genes = com.$store.state.active_subset;

      if (!genes || com.loading_state) {
        alert("please select a subset or pathway to apply enrichment");
        return;
      }

      //Adding proteins and species to formdata
      var formData = new FormData();
      formData.append("genes", genes);
      formData.append("species_id", com.gephi_data.nodes[0].species);
      formData.append(
        "mapping",
        JSON.stringify(com.gephi_data.settings["gene_alias_mapping"])
      );

      com.loading_state = true;
      //POST request for generating pathways
      com.sourceToken = this.axios.CancelToken.source();
      com.axios
        .post(com.api.subgraph, formData, {
          cancelToken: com.sourceToken.token,
        })
        .then((response) => {
          com.set_dict.add({
            name: `layer ${com.layer}`,
            genes: genes,
            terms: response.data.sort((t1, t2) => t1.fdr_rate - t2.fdr_rate),
            status: false,
            information: false,
            stats: com.get_significant_words(response.data),
          });
          com.layer += 1;
          com.loading_state = false;
        });
    },
    remove_set(entry) {
      if (entry.status) this.emitter.emit("enrichTerms", null);
      this.set_dict.delete(entry);
    },
    set_active(entry) {
      for (var layer of this.set_dict) {
        if (layer != entry) layer.status = false;
      }

      if (!entry.status) {
        this.emitter.emit("searchSubset", {
          subset: this.activate_genes(entry.genes),
          mode: "protein",
        });
        this.emitter.emit("enrichTerms", entry.terms);
      } else {
        this.emitter.emit("searchSubset", { subset: null, mode: "protein" });
        this.emitter.emit("enrichTerms", null);
      }
      entry.status = !entry.status;
    },
    activate_genes(genes) {
      var com = this;
      var subset = [];
      var genes_set = new Set(genes);

      com.gephi_data.nodes.forEach((node) => {
        if (genes_set.has(node.attributes["Name"])) {
          subset.push(node);
        }
      });

      return subset;
    },
    get_significant_words(term_set) {
      const namesArray = term_set.map((obj) => obj.name);
      const text = namesArray.join(", ");

      if (text == null) return null;

      const topWords = this.getTopWords(text);

      return topWords;
    },
    getTopWords(text) {
      const stopwords = new Set([
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "should",
        "now",
      ]);

      // Step 1: Tokenize the text and filter out stopwords
      const words = text
        .toLowerCase()
        .match(/\b\w+\b/g)
        .filter((word) => !stopwords.has(word));

      // Step 2: Count word frequencies
      const wordCount = {};
      words.forEach((word) => {
        if (wordCount[word]) {
          wordCount[word]++;
        } else {
          wordCount[word] = 1;
        }
      });

      // Step 3: Calculate percentages
      const totalWords = words.length;
      const wordPercentages = {};
      Object.keys(wordCount).forEach((word) => {
        const percentage = (wordCount[word] / totalWords) * 100;
        wordPercentages[word] = percentage.toFixed(2); // Limiting to 2 decimal places
      });

      // Step 4: Sort words by frequency and select top 10
      const sortedWords = Object.keys(wordPercentages)
        .sort((a, b) => wordCount[b] - wordCount[a])
        .slice(0, 5);

      // Step 5: Prepare and return results
      const topWordsWithPercentages = sortedWords.map(
        (word) => `${word}: ${wordPercentages[word]}%`
      );
      return topWordsWithPercentages;
    },
  },
};
</script>

<style>
#pathways-set {
  width: 100%;
  height: 100%;
  cursor: default;
  font-family: "ABeeZee", sans-serif;
}

.pathway-apply-section {
  width: 100%;
  height: 87.65%;
  border-radius: 5px;
  position: absolute;
}

.generate-set-button {
  display: inline-flex;
  margin: 1vw 0 1vw 0;
  height: 1vw;
  width: 100%;
  padding: 0 2vw 0 2vw;
}

.generate-set-button .export-text {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0a0a1a;
  font-size: 0.7vw;
}

.pathway-apply-section a {
  color: white;
  text-decoration: none;
}

.pathway-apply-section .results {
  height: 100%;
  overflow: scroll;
}
.pathway-apply-section .sorting a {
  color: rgba(255, 255, 255, 0.7);
}

.set-table {
  display: -webkit-flex;
  padding-top: 0.4vw;
}

#pathways-set .pathway-text {
  width: 80%;
  display: flex;
  align-items: center;
  white-space: nowrap;
  overflow: hidden; /* Hide overflow content */
  text-overflow: ellipsis;
  margin-left: 2%;
}
#pathways-set .pathway-text input[type="text"] {
  width: 100%;
  font-size: 0.85vw;
  background: none;
  color: white;
  cursor: default;
  font-family: "ABeeZee", sans-serif;
  border: none;
}
#pathways-set .pathway-text span {
  font-size: 0.7vw;
  margin-left: 4%;
  color: rgba(255, 255, 255, 0.7);
}

#pathways-set .pathway-text a {
  cursor: default;
}

/* bookmark styles */

table {
  display: flex;
  width: 100%;
}

:focus {
  outline: 0 !important;
}

table tbody {
  width: 100%;
}
.set-table td:first-child {
  width: 15.41%;
  align-self: center;
}
.set-table td:nth-child(2) {
  color: #fff;
  font-size: 0.9vw;
  width: 88.55%;
  overflow: hidden;
  align-self: center;
}
.set-table td:last-child {
  font-size: 0.9vw;
  color: white;
  width: 21.04%;
  padding: 0.1vw;
  align-self: center;
}

.expanded td:first-child,
.expanded td:nth-child(2),
.expanded td:nth-child(3),
.expanded td:nth-child(4),
.expanded td:last-child {
  color: #fff;
  width: 20%;
  overflow: hidden;
  align-self: center;
}

.favourite-symbol {
  width: 100%;
  height: 100%;
  justify-content: center;
  text-align: center;
  position: relative;
  display: flex;
}
.custom-checkbox {
  position: relative;
  display: inline-block;
  cursor: default;
}

.custom-icons {
  position: relative;
  display: inline-block;
  cursor: default;
  padding-right: 0.5vw;
}

.active-image {
  display: block;
  width: 0.9vw;
  height: 0.9vw;
  background-color: white;
  -webkit-mask: url(@/assets/pathwaybar/active.png) no-repeat center;
  mask: url(@/assets/pathwaybar/active.png) no-repeat center;
  mask-size: 0.9vw;
  background-repeat: no-repeat;
}

.delete-image {
  display: block;
  width: 0.9vw;
  height: 0.9vw;
  background-color: white;
  -webkit-mask: url(@/assets/pathwaybar/delete.png) no-repeat center;
  mask: url(@/assets/pathwaybar/delete.png) no-repeat center;
  mask-size: 0.9vw;
  background-repeat: no-repeat;
}

.expand-image {
  display: block;
  width: 0.9vw;
  height: 0.9vw;
  background-color: white;
  -webkit-mask: url(@/assets/toolbar/menu-burger.png) no-repeat center;
  mask: url(@/assets/toolbar/menu-burger.png) no-repeat center;
  mask-size: 0.9vw;
  background-repeat: no-repeat;
}

.checked {
  background-color: #ffa500;
}

.selected {
  background-color: rgba(255, 0, 0, 0.7);
}

.tool-set-section-graph {
  display: grid;
  grid-template-columns: 0.5fr 0.5fr;
  padding: 1vw 1vw 1vw 1vw;
  width: 100%;
  flex-shrink: 0;
}

.coloumn-set-button {
  padding-right: 0.5vw;
  display: grid;
  row-gap: 1vw;
  z-index: 9999;
}

.information-set {
  font-size: 0.5vw;
  display: flex;
  justify-content: center;
  text-align: center;
  padding: 0.2vw;
}

.expanded {
  display: -webkit-flex;
  padding: 0 2vw 0 2vw;
  background: rgba(255, 255, 255, 0.1);
  background-clip: content-box;
}
</style>
