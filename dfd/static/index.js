(function () {
    'use strict';


    const gContainerView = document.querySelector('#container-view');


    async function main () {
        initialize();
        await loadFilters();
    }


    function initialize () {
        let buttonAdd = document.querySelector('#button-add');
        let inputAdd = document.querySelector('#input-add');
        buttonAdd.addEventListener('click', async (event) => {
            let newFilter = inputAdd.value;
            await addFilter(newFilter);
            inputAdd.value = '';
        });
    }


    async function loadFilters () {
        let rv = await fetch('/api/v1/filters');
        rv = await rv.json();
        Object.keys(rv).forEach((id) => {
            const filter = rv[id];
            const widget = createWidget(id, filter);
            gContainerView.appendChild(widget);
        });
    }


    function createWidget (id, filter) {
        let d = document.createElement('div');
        d.dataset.id = id;

        let input = document.createElement('input');
        input.value = filter;
        d.appendChild(input);

        let button = document.createElement('button');
        button.textContent = 'update';
        button.addEventListener('click', async (event) => {
            const newFilter = input.value;
            await updateFilter(id, newFilter);
        });
        d.appendChild(button);

        return d;
    }


    async function addFilter (newFilter) {
        let id = await fetch('/api/v1/filters', {
            method: 'POST',
            body: newFilter,
        });
        id = await id.json();

        const widget = createWidget(id, newFilter);
        gContainerView.appendChild(widget);
    }


    async function updateFilter (id, newFilter) {
        await fetch(`/api/v1/filters/${id}`, {
            method: 'PUT',
            body: newFilter,
        });
    }


    return main();

})();
