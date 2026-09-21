const progressDataElement = document.getElementById(
    "progress-data"
);

const metricSelect = document.getElementById(
    "metric-select"
);

const chart = document.getElementById(
    "progress-chart"
);

const metricDescription = document.getElementById(
    "metric-description"
);


const progressData = JSON.parse(
    progressDataElement.textContent
);


const metrics = {
    best_weight: {
        label: "Best weight",
        suffix: " kg",
        description:
            "The heaviest weight recorded in each session."
    },

    volume: {
        label: "Total volume",
        suffix: " kg",
        description:
            "The total recorded weight multiplied by repetitions."
    },

    best_reps: {
        label: "Best reps",
        suffix: " reps",
        description:
            "The highest repetitions recorded in a single set."
    }
};


const SVG_NAMESPACE =
    "http://www.w3.org/2000/svg";


function createSvgElement(name, attributes = {}) {
    const element = document.createElementNS(
        SVG_NAMESPACE,
        name
    );

    Object.entries(attributes).forEach(
        function ([key, value]) {
            element.setAttribute(
                key,
                value
            );
        }
    );

    return element;
}


function addText(
    parent,
    text,
    x,
    y,
    className,
    anchor = "start"
) {
    const element = createSvgElement(
        "text",
        {
            x: x,
            y: y,
            class: className,
            "text-anchor": anchor
        }
    );

    element.textContent = text;

    parent.appendChild(
        element
    );

    return element;
}


function formatValue(value, suffix) {
    const rounded = Number.isInteger(value)
        ? value
        : Number(value.toFixed(2));

    return `${rounded}${suffix}`;
}


function renderChart() {
    const metric = metricSelect.value;
    const metricDetails = metrics[metric];

    metricDescription.textContent =
        metricDetails.description;

    while (chart.firstChild) {
        chart.removeChild(
            chart.firstChild
        );
    }

    const title = createSvgElement(
        "title",
        {
            id: "progress-chart-title"
        }
    );

    title.textContent =
        `${metricDetails.label} progress`;

    chart.appendChild(
        title
    );


    const description = createSvgElement(
        "desc",
        {
            id: "progress-chart-description"
        }
    );

    const exerciseName =
        chart.dataset.exerciseName;

    description.textContent =
        `${metricDetails.label} across recorded sessions `
        + `for ${exerciseName}.`;

    chart.appendChild(
        description
    );


    const points = progressData.filter(
        function (session) {
            return (
                session[metric] !== null
                && session[metric] !== undefined
            );
        }
    );

    if (points.length === 0) {
        addText(
            chart,
            "No data is available for this metric.",
            450,
            180,
            "chart-empty-text",
            "middle"
        );

        return;
    }


    const width = 900;
    const height = 360;

    const padding = {
        top: 30,
        right: 30,
        bottom: 65,
        left: 75
    };

    const graphWidth =
        width
        - padding.left
        - padding.right;

    const graphHeight =
        height
        - padding.top
        - padding.bottom;


    const values = points.map(
        function (session) {
            return Number(
                session[metric]
            );
        }
    );

    const highestValue = Math.max(
        ...values
    );

    let yMaximum;

    if (metric === "best_reps") {
        yMaximum = Math.max(
            Math.ceil(highestValue + 1),
            5
        );
    } else {
        yMaximum =
            highestValue > 0
                ? highestValue * 1.1
                : 1;
    }

    const gridGroup = createSvgElement(
        "g"
    );

    chart.appendChild(
        gridGroup
    );


    const tickCount = 5;

    for (
        let tick = 0;
        tick <= tickCount;
        tick += 1
    ) {
        const ratio =
            tick / tickCount;

        const y =
            padding.top
            + graphHeight
            - ratio * graphHeight;

        let value =
            ratio * yMaximum;

        if (metric === "best_reps") {
            value = Math.round(
                value
            );
        }

        const line = createSvgElement(
            "line",
            {
                x1: padding.left,
                y1: y,
                x2: width - padding.right,
                y2: y,
                class: "chart-grid-line"
            }
        );

        gridGroup.appendChild(
            line
        );


        addText(
            gridGroup,
            formatValue(
                value,
                metricDetails.suffix
            ),
            padding.left - 12,
            y + 4,
            "chart-axis-label",
            "end"
        );
    }


    const chartPoints = points.map(
        function (session, index) {
            let x;

            if (points.length === 1) {
                x =
                    padding.left
                    + graphWidth / 2;

            } else {
                x =
                    padding.left
                    + (
                        index
                        / (points.length - 1)
                    )
                    * graphWidth;
            }

            const value =
                Number(
                    session[metric]
                );

            const y =
                padding.top
                + graphHeight
                - (
                    value / yMaximum
                )
                * graphHeight;

            return {
                x: x,
                y: y,
                value: value,
                session: session
            };
        }
    );


    if (chartPoints.length > 1) {
        const linePoints = chartPoints
            .map(
                function (point) {
                    return (
                        `${point.x},${point.y}`
                    );
                }
            )
            .join(" ");

        const line = createSvgElement(
            "polyline",
            {
                points: linePoints,
                class: "chart-progress-line"
            }
        );

        chart.appendChild(
            line
        );
    }


    const labelEvery = Math.max(
        1,
        Math.ceil(
            chartPoints.length / 7
        )
    );


    chartPoints.forEach(
        function (point, index) {
            const circle = createSvgElement(
                "circle",
                {
                    cx: point.x,
                    cy: point.y,
                    r: 6,
                    class: "chart-progress-point"
                }
            );

            const tooltip = createSvgElement(
                "title"
            );

            tooltip.textContent =
                `${point.session.full_date}: `
                + formatValue(
                    point.value,
                    metricDetails.suffix
                );

            circle.appendChild(
                tooltip
            );

            chart.appendChild(
                circle
            );


            if (
                index % labelEvery === 0
                || index === chartPoints.length - 1
            ) {
                addText(
                    chart,
                    point.session.date,
                    point.x,
                    height - 28,
                    "chart-axis-label",
                    "middle"
                );
            }
        }
    );


    const firstPoint =
        chartPoints[0];

    const lastPoint =
        chartPoints[
            chartPoints.length - 1
        ];


    if (chartPoints.length > 1) {
        addText(
            chart,
            formatValue(
                firstPoint.value,
                metricDetails.suffix
            ),
            firstPoint.x,
            firstPoint.y - 14,
            "chart-value-label",
            "middle"
        );

        addText(
            chart,
            formatValue(
                lastPoint.value,
                metricDetails.suffix
            ),
            lastPoint.x,
            lastPoint.y - 14,
            "chart-value-label",
            "middle"
        );
    }
}


const defaultMetric =
    metricSelect.dataset.defaultMetric.trim();

if (
    defaultMetric
    && metricSelect.querySelector(
        `option[value="${defaultMetric}"]`
    )
) {
    metricSelect.value =
        defaultMetric;
}


metricSelect.addEventListener(
    "change",
    renderChart
);


renderChart();