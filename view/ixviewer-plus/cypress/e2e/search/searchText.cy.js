import { selectors } from "../../utils/selectors.mjs"
import { readFilingData, readFilingDataAccNum } from '../../dataPlus/filingsFunnel.js'
import { search, assertSearchResultCount } from "../../utils/utils.mjs"

let mitkFiling = readFilingDataAccNum('000080786323000002');
// http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm
let nv8k = readFilingDataAccNum('000106299321011674');
let strata = readFilingDataAccNum('000121390021056659');
// http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/1517396/000121390021056659/stratasys-6k.htm


describe(`Search for specific text in specific filings`, () => {

    it(`Search for zip value`, () => {

        cy.loadFiling(mitkFiling)
        cy.get(selectors.factCountClock, { timeout: Number(mitkFiling.timeout) }).should('not.exist')
        cy.get(selectors.searchHourglass).should('exist');
        cy.get(selectors.searchHourglass).should('not.be.visible');

        cy.get(selectors.search).type('92101')
        // cy.get(selectors.submitSearchButton).click()
        cy.get(selectors.search).type('{enter}')

        cy.get(selectors.searchHourglass).should('not.be.visible')
        cy.get(selectors.factCountBadge).should('have.text', '1')
    })

    it(`Search for 'NV' fact`, () => {
        cy.loadFiling(nv8k)
        cy.get(selectors.factCountClock, { timeout: Number(nv8k.timeout) }).should('not.exist')

        cy.get(selectors.search).type('NV')
        // cy.get(selectors.submitSearchButton).click()
        cy.get(selectors.search).type('{enter}')

        cy.get(selectors.factCountBadge).should('have.text', '1')
    })

    it('Search bar should be able to find facts based on transformed name (e.g. searching "NY" will find "New York")', () => {
        cy.loadByAccessionNum('000182912623008291')
        // http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/1653876/000182912623008291/momentous_10kt.htm

        cy.get(selectors.search).type('NY', { force: true })

        cy.get(selectors.search).type('{enter}')
        cy.wait(200);

        cy.get('#fact-identifier-109')
            .should('have.attr', 'highlight-fact', 'true')
    })
})


describe(`Search for specific text in specific filings Reference search option`, () => {
    beforeEach(() => {
        cy.loadByAccessionNum('000143774923034166').then(() => {
            // http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/1415744/000143774923034166/nmex20231031_10q.htm

            // Uncheck "Include Fact Name", "Include Fact Content", "Include Labels"
            cy.get(selectors.searchSettingsGear).click().then(() => {
                cy.get('input[name="search-options"][value="1"]').click().then(() => {
                    cy.get('input[name="search-options"][value="1"]').should('not.be.checked')
                })
                cy.get('input[name="search-options"][value="2"]').click().then(() => {
                    cy.get('input[name="search-options"][value="2"]').should('not.be.checked')
                })

                cy.get('input[name="search-options"][value="3"]').click().then(() => {
                    cy.get('input[name="search-options"][value="3"]').should('not.be.checked')
                })
                // Check "Include References"
                cy.get('input[name="search-options"][value="6"]').click().then(() => {
                    cy.get('input[name="search-options"][value="6"]').should('be.checked')
                })
            })
        })


    })
    it('Search "SEC" for Publisher references', () => {
        search("SEC")
        assertSearchResultCount(11)

        cy.get(selectors.searchSettingsGear).click().then(() => {
            // Check "Fact Name"
            cy.get('input[name="search-options"][value="1"]').click().then(() => {
                cy.get('input[name="search-options"][value="1"]').should('be.checked')
            })
        })
        assertSearchResultCount(19)

    })

     it('Search "S99" for Section references', () => {
        search("S99")
        assertSearchResultCount(152)

        cy.get(selectors.searchSettingsGear).click().then(() => {
            // Check "Fact Name"
            cy.get('input[name="search-options"][value="1"]').click().then(() => {
                cy.get('input[name="search-options"][value="1"]').should('be.checked')
            })
        })
        assertSearchResultCount(152)

    })
})