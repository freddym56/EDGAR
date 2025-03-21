import * as bootstrap from "bootstrap";
import * as devJSON from "./input.json";
import * as nomnoml from 'nomnoml';

/**
 * Description
 * @returns {any} -> generates table of filings at http://localhost:3000/ix.xhtml
 */
export class Development {
    constructor() {
        if (!PRODUCTION) {
            this.createTabs();
        }
    }

    createTabs() {
        const container = document.getElementById(`dynamic-xbrl-form`);
        const ul = 
            `<ul class="nav nav-tabs" id="tabs" role="tablist"">
            </ul>`;
        
        const parser = new DOMParser();
        const labelDocUl = parser.parseFromString(ul,'text/html');

        const ulElement = labelDocUl.querySelector('body > ul') as HTMLElement;  

        let div = '';
        let divElement = '' as unknown as HTMLElement;

        const tabs = ['Test Filings', 'Flow Chart(s)'];

        tabs.forEach((current, index) => {
            const activeVar = index === 0 ? 'active' : '';
            const li = 
            `<li class="nav-item" role="presentation">
                <button class="nav-link ${activeVar}" id="tab-${index}" 
                    data-bs-toggle="tab" data-bs-target="#tab-${index}-pane" type="button">${current}</button>
            </li>`;
            
            const labelDocLi = parser.parseFromString(li,'text/html');
            const liElement = labelDocLi.querySelector('body > li') as HTMLElement;   
            
            ulElement.append(liElement);

        });

        div = 
        `<div class="tab-content nav-tabs" id="tab-content">

        </div>`;

        const labelDocDiv = parser.parseFromString(div,'text/html');
        divElement = labelDocDiv.querySelector('body > div') as HTMLElement;  

        tabs.forEach((_current, index) => {
            const showVar = index === 0 ? 'show' : '';
            const activeVar = index === 0 ? 'active' : '';

            div = 
            `<div class="tab-pane fade ${showVar} ${activeVar}" id="tab-${index}-pane"">
            </div>`;

            const labelDocDiv = parser.parseFromString(div,'text/html');
            const divElement2 = labelDocDiv.querySelector('body > div') as HTMLElement;  

            divElement.append(divElement2);
        });    
 
     
        container?.append(ulElement);
        container?.append(divElement);
        this.createTable('tab-0-pane');
        this.createFlowCharts('tab-1-pane');

        const triggerTabList = Array.from(document.querySelectorAll('#tabs button'));
        triggerTabList.forEach((current) => {
            const tabTrigger = new bootstrap.Tab(current);
            current.addEventListener('click', (event) => {
                event.preventDefault();
                tabTrigger.show();
            })
        });


    }

    createTable(containerId: string) {
        const arrayOfJSON = Object.entries(devJSON).map((current) => {
            return {
                ...current[1], ...{ id: current[0] }
            }
        });
        arrayOfJSON.pop();
        arrayOfJSON.sort((a, b) => +b.important - +a.important);

        const container = document.getElementById(containerId);

        const table = document.createElement(`table`);
        table.classList.add('table');
        table.classList.add('table-striped-columns');
        table.classList.add('table-hover');
        const thead = document.createElement(`thead`);
        thead.classList.add('sticky-top');
        const tr1 = document.createElement(`tr`);
        const ths = [
            'ID', 'Name', 'Form', 'Version',
            'Important?', 'Multi-File?', 'Multi-Instance?',
            'ContextRefs', 'SEC', 'DEV'];
        ths.forEach((current) => {
            const th = document.createElement(`th`);
            const text = document.createTextNode(current);
            th.append(text)
            tr1.append(th)
        });
        thead.append(tr1);
        table.append(thead)
        const tbody = document.createElement(`tbody`);
        arrayOfJSON.forEach((current) => {
            if (current.id && current.version && current.sec && current.local) {
                const tr = document.createElement('tr');

                const id = document.createElement('td');
                const idText = document.createTextNode(current['id']);
                id.append(idText);
                tr.append(id);

                const name = document.createElement('td');
                const nameText = document.createTextNode(current['name']);
                name.append(nameText);
                tr.append(name);

                const form = document.createElement('td');
                const formText = document.createTextNode(current['form']);
                form.append(formText);
                tr.append(form);

                const version = document.createElement('td');
                const versionText = document.createTextNode(current['version']);
                version.append(versionText);
                tr.append(version);


                const important = document.createElement('td');
                important.classList.add('text-center');
                const importantText = document.createTextNode(
                    current.important ? '\u2714' : ''
                );
                important.append(importantText);
                tr.append(important);


                const multiple = document.createElement('td');
                multiple.classList.add('text-center');
                const multipleText = document.createTextNode(
                    current.local.length > 1 ? '\u2714' : ''
                );
                multiple.append(multipleText);
                tr.append(multiple);

                const instance = document.createElement('td');
                instance.classList.add('text-center');
                const instanceText = document.createTextNode(
                    current.multiple_instance ? '\u2714' : ''
                );
                instance.append(instanceText);
                tr.append(instance);

                const contextrefs = document.createElement('td');
                contextrefs.classList.add('text-center');
                const contextrefsText = document.createTextNode(current['contextrefs'].toLocaleString('en-US'));
                contextrefs.append(contextrefsText);
                tr.append(contextrefs);


                const sec = document.createElement('td');
                if (current['sec'].length) {
                    const asec = document.createElement('a');
                    asec.setAttribute('href', `https://www.sec.gov/ix?doc=${current['sec'][0]}`);
                    // https://www.sec.gov/ix?doc=https://www.sec.gov/Archives/edgar/data/7084/000000708423000037/adm-20231024.htm
                    asec.setAttribute(`target`, `_blank`);
                    const viewerTextsec = document.createTextNode(`Go See`);
                    asec.append(viewerTextsec);
                    sec.append(asec);
                }
                tr.append(sec);


                const local = document.createElement('td');
                if (current['local'].length) {
                    const alocal = document.createElement('a');
                    // alocal.setAttribute('href', `${window.location.href}?doc=${current['local'][0].replace('/src', '')}`);
                    alocal.setAttribute('href', `${window.location.href}?doc=${current['local'][0].replace('/Archives/edgar/data/', '/ixdocs/WebContent/documents/')}`);
                    alocal.setAttribute(`target`, `_blank`);
                    const viewerTextlocal = document.createTextNode(`Go See`);
                    alocal.append(viewerTextlocal);
                    local.append(alocal);
                }
                tr.append(local);

                tbody.append(tr);
            }
        })
        table.append(tbody);
        container?.append(table);
    }

    createFlowCharts(containerId: string) {
        this.firstFlowChart(containerId);
        this.secondFlowChart(containerId);
    }

    firstFlowChart(containerId: string) {
        const container = document.getElementById(containerId);
        const rightContainer = document.createElement('div');
        rightContainer.classList.add('w-50');
        rightContainer.classList.add('h-100');
        rightContainer.classList.add('float-start');
        const h3 = document.createElement('h3');
        const h3Text = document.createTextNode(`Simplified Overview`);
        h3.append(h3Text);
        rightContainer.append(h3);
        const canvas = document.createElement('canvas');
        canvas.setAttribute('id', 'target-canvas2');
        canvas.classList.add('h-50');
        canvas.classList.add('overflow-y-auto');
        rightContainer.append(canvas);

        const ul = document.createElement('ul');
        ul.classList.add('list-group');
        const text = [
            `* = This file will only ever be Fetched one time`,
            `** = There are one or many files, all will be Fetched that exsist for the specific Instance`,
            `*** = There are one of these files per Instance, and will be Fetched for each specific Instance`
        ];
        text.forEach((current) => {
            const li = document.createElement('li');
            li.classList.add('list-group-item');
            const liText = document.createTextNode(current);

            li.append(liText);
            ul.append(li);
        });
        rightContainer.append(ul);
        container?.append(rightContainer);
        const canvasElement = document.getElementById('target-canvas2');
        const source = `
        [<start>] -> 
        [<table> Get URL Params | XHTML | MetaLinks] ->
        [Web Worker?] -> [Obtain External Files & Prepare Data Structure(s)]
        [Obtain External Files & Prepare Data Structure(s) |
            [MetaLinks.json*] -> [XHTML(s)**] -> [Extract Sections] -> [Merge Fact Data]
            [MetaLinks.json*] -> [XML Instance***] -> [Extract Sections]-> [Merge Fact Data]
            [Merge Fact Data] -> [Prepare XHTMLs with fact attributes]
        ] -> 
        [<table> Return Instance Data | XHTML(s) | Facts | Sections] -> 
        [<table> Store Data | Add XHTML(s) to DOM | Store Facts & Set FlexSearch | Set Sections]
        [<table> Multi-Instance (User Interaction) | Sections | Tab Bar] -> [Web Worker?]
        `;
        nomnoml.draw(canvasElement as HTMLCanvasElement, source);
    }

    secondFlowChart(containerId: string) {
        const container = document.getElementById(containerId);
        const rightContainer = document.createElement('div');
        rightContainer.classList.add('w-50');
        rightContainer.classList.add('h-100');
        rightContainer.classList.add('float-start');
        const h3 = document.createElement('h3');
        const h3Text = document.createTextNode(`Required Files (XHTML(s), XML(s), JSON)`);
        h3.append(h3Text);
        rightContainer.append(h3);
        // const canvas = document.createElement('canvas');
        // canvas.setAttribute('id', 'target-canvas2');
        // canvas.classList.add('h-100');
        // canvas.classList.add('overflow-y-auto');
        // rightContainer.append(canvas);

        const ol = document.createElement('ol');
        ol.classList.add('list-group');
        ol.classList.add('list-group-numbered');
        const text = [
            {
                title: `XHTML File(s)`,
                content: `XHTML file(s). 
                This is the file that the user can see and interact with. 
                Atleast one file must exist, there may also be many. 
                We get all XHTML Files onload of the application.`
            },
            {
                title: `Meta Links`,
                content: `JSON File. 
                This file holds additional information for the facts that exsist within the filing. 
                Also has supplemental information for the Sections menu.`
            },
            {
                title: `Filing Summary`,
                content: `XML File. 
                This file contains the necessary information to build the Sections menu.`
            },
            {
                title: `XBRL Instance`,
                content: `XML File. 
                This file holds the majority of the information for the Facts that exsist within the Filing.`
            },
        ];
        text.forEach((current) => {
            const li = 
            `<li class="list-group-item d-flex justify-content-between align-items-start">
                <div class="ms-2 me-auto ">${current.content}
                    <div class="fw-bold">${current.title}</div>
                </div>
            </li>`;

            const parser = new DOMParser();
            const labelDocLi = parser.parseFromString(li,'text/html');
    
            const liElement = labelDocLi.querySelector('body > li') as HTMLElement;  

            ol.append(liElement);
        });
        rightContainer.append(ol);
        container?.append(rightContainer);
    }

}
