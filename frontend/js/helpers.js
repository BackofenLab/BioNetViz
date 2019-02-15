
var colors = {
    protein: "rgb(82,182,229)",
    pathway: "rgb(242,181,0)",
    white: "rgb(255,255,255)",
    black: "rgb(0,0,0)",
    gray: "rgb(198,198,198)"
};

function make_graph_layout(data) {
    // TODO
}

function generate_legend(legend){
    var container = $("#legend");

    var html = "Score:<br/>";
    html += "0.0 <div id=\"grad\"></div> 1.0<br/>";

    html += "<ul class=\"legend-entry\">";

    for (var name in legend) {
        var color = legend[name];
        html += "<li><span style=\"background-color: " + color + ";\"></span> " + name + "</li>";
    }

    html += "</ul>";

    container.html(html);
}

function get_edge_color(score) {

    function color_to_string(color) {
        return "rgb(" + color.r + "," + color.g + "," + color.b + ")";
    }

    function weight_average_colors(c1, c2, w) {
        return {
            r: Math.floor((1 - w) * c1.r + w * c2.r),
            g: Math.floor((1 - w) * c1.g + w * c2.g),
            b: Math.floor((1 - w) * c1.b + w * c2.b)
        }
    }

    var high = {r: 255, g: 0, b: 0};
    var medium = {r: 0, g: 255, b: 0};
    var low = {r: 0, g: 0, b: 255};

    var color = null;

    if (score <=0) {
        color = color_to_string(low);
    }
    else if (score > 0 && score <= 500) {
        var w = score / 500;
        color = weight_average_colors(low, medium, w);
    }
    else if (score > 500 && score <= 1000) {
        var w = (score - 500) / 500;
        color = weight_average_colors(medium, high, w);
    }
    else {
        color = high;
    }

    return color_to_string(color);
}

function get_tooltip(id, text) {
    var div = document.createElement("div");
    div.style.width = "500px";

    var html = "<b>" + id + "</b>";
    html += "<br/><br/>";
    html += text;

    div.innerHTML = html;
    div.style.wordWrap = "break-word";
    div.style.whiteSpace = "pre-wrap";
    return div;
}

$(document).ready(function (){
    // generate legend
    generate_legend({
        "Protein": colors.protein,
        "Pathway": colors.pathway,
        "Class": colors.gray
    });

    // progress bar
    $("#progressbar").progressbar({
        value: 0
    });
});
