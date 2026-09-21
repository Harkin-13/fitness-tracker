const tabs = document.querySelectorAll(
    ".workout-tab"
);

const panels = document.querySelectorAll(
    ".workout-panel"
);

const workoutControls =
    document.querySelectorAll(
        "[data-workout-controls]"
    );


function getPanelId(tab) {
    return tab.dataset.panel.trim();
}


function getControlsPanelId(controls) {
    return controls.dataset
        .workoutControls
        .trim();
}


function activateTab(tab) {
    const panelId = getPanelId(tab);


    tabs.forEach(
        function (otherTab) {
            const isActive =
                otherTab === tab;

            otherTab.classList.toggle(
                "active",
                isActive
            );

            otherTab.setAttribute(
                "aria-selected",
                isActive
                    ? "true"
                    : "false"
            );

            otherTab.tabIndex =
                isActive
                    ? 0
                    : -1;
        }
    );


    panels.forEach(
        function (panel) {
            panel.hidden =
                panel.id !== panelId;
        }
    );


    workoutControls.forEach(
        function (controls) {
            controls.hidden =
                getControlsPanelId(
                    controls
                ) !== panelId;
        }
    );
}


tabs.forEach(
    function (tab) {
        tab.addEventListener(
            "click",
            function () {
                activateTab(
                    tab
                );
            }
        );


        tab.addEventListener(
            "keydown",
            function (event) {
                if (
                    event.key !== "ArrowLeft"
                    && event.key !== "ArrowRight"
                ) {
                    return;
                }

                event.preventDefault();

                const tabArray =
                    Array.from(
                        tabs
                    );

                const currentIndex =
                    tabArray.indexOf(
                        tab
                    );

                let nextIndex;

                if (
                    event.key
                    === "ArrowRight"
                ) {
                    nextIndex =
                        (
                            currentIndex + 1
                        )
                        % tabArray.length;
                } else {
                    nextIndex =
                        (
                            currentIndex
                            - 1
                            + tabArray.length
                        )
                        % tabArray.length;
                }

                const nextTab =
                    tabArray[
                        nextIndex
                    ];

                activateTab(
                    nextTab
                );

                nextTab.focus();
            }
        );
    }
);