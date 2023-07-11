(function ($) {
    "use strict";

    function ChartManager() {
        this.charts = [];
    }

    ChartManager.prototype.init = function () {
        this.initCharts();
    };

    ChartManager.prototype.initCharts = function () {
        var defaultColors = ["#727cf5", "#0acf97"];
        var $chartContainer = $("#visualisierung_der_voraussichtlichen_amortisationszeit");
        var customColors = $chartContainer.data("colors");
        var colors = customColors ? customColors.split(",") : defaultColors;

        var options = {
            chart: {
                height: 361,
                type: "line",
                dropShadow: {
                    enabled: true,
                    opacity: 0.2,
                    blur: 7,
                    left: -7,
                    top: 7
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                curve: "smooth",
                width: 4
            },
            series: [
                {
                    name: "ohne PVA",
                    data: data["arbeitsListe"]
                }, 
                {
                    name: "mit PVA",
                    data: data["restListe"]
                }
            ],
            colors: colors,
            zoom: {
                enabled: false
            },
            xaxis: {
                type: "categories",
                categories: Array.from({length: data["zeitraum"]}, (_, i) => i + 1),
                tooltip: {
                    enabled: false
                },
                axisBorder: {
                    show: false
                },
                title: {
                    text: "Jahre"
                }
            },
            yaxis: {
                labels: {
                    formatter: function (value) {
                        return value + "k";
                    },
                    offsetX: -15
                },
                title: {
                    text: "Kosten in €"
                }
            }
        };
        
        var chart = new ApexCharts($chartContainer[0], options);
        chart.render();

        this.charts.push(chart);
    };

    $(document).ready(function () {
        var manager = new ChartManager();
        manager.init();
        $.CrmManagement = manager;
    });

}(jQuery));