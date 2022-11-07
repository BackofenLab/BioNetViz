Vue.component("search", {
    props: ["gephi_json"],
    data: function() {
        return {
            input: null,
            state: null,
            results: null,
            exactMatch: false,
            lastSearch: "",
            searching: false,
            matches: [],
            message: "",
            search_check: false,
        }
    },
    methods: {
        select_node: function(id) {
            var com = this;
            com.$emit("active-node-changed", id);
        },
        close: function () {
            var com = this;

            com.state.removeClass("searching");
            com.results.hide();
            com.searching = !1;
            com.input.val("");
            com.select_node(null);
        },
        clean: function () {
            var com = this;

            com.results.hide();
            com.state.removeClass("searching");
            com.input.val("");
        },
        search: function (query) {
            var com = this;

            com.matches = [];
            com.message = "";
            com.searching = true;
            com.lastSearch = query;
            com.results.show();

            var regex = RegExp(com.exactMatch ? ("^" + query + "$").toLowerCase() : query.toLowerCase());

            if (query.length < 3) {
                com.message = "Minimum 3 letters required.";
                return;
            }

            sigma_instance.graph.nodes().forEach(function (n) {
                if (regex.test(n.label.toLowerCase()))
                    com.matches.push({
                        id: n.id,
                        name: n.label
                    })
            });

            if (com.matches.length == 1) {
                com.$emit("active-node-changed", com.matches[0].id);
            }
        }
    },
    mounted: function() {
        var com = this;

        var a = $("#search");
        com.input = a.find("input");
        com.state = a.find(".state");
        com.results = a.find(".results");

        com.input.focus(function () {
            var a = $(this);
            a.data("focus") || (a.data("focus", !0), a.removeClass("empty"));
            com.clean()
        });

        com.input.keydown(function (a) {
            if (13 == a.which) return com.state.addClass("searching"), com.search(com.input.val()), !1
        });

    },
    template: `
            <div v-show="gephi_json != null" id="search" class="toolbar-search">
                <div class="search-field">
                <input type="text" value="Search nodes by name" class="search_empty"/>
                </div>
                <div class="results">
                    <i v-if="message.length > 0">{{message}}</i>
                    <div v-for="entry in matches">
                        <a href="#" v-on:click="select_node(entry.id)">{{entry.name}}</a>
                    </div>
                    <div v-if="matches.length == 0">
                        <i>No results found.</i>
                    </div>
                </div>
            </div>
    `
});