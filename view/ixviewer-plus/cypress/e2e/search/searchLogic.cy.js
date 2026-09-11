import { selectors } from "../../utils/selectors.mjs"
import { search, assertSearchResultCount } from "../../utils/utils.mjs"

describe(`Search text with logical operators in specific filings`, () => {
    beforeEach(() => {
        cy.loadByAccessionNum('000143774923034166').then(() => {
            cy.get(selectors.searchHourglass).should('exist');
            cy.get(selectors.searchHourglass).should('not.be.visible');

            // Uncheck "Include Fact Name" and "Include Fact Content"
            cy.get(selectors.searchSettingsGear).click().then(() => {
                cy.get('input[name="search-options"][value="2"]').click().then(() => {
                    cy.get('input[name="search-options"][value="2"]').should('not.be.checked')
                })

                cy.get('input[name="search-options"][value="3"]').click().then(() => {
                    cy.get('input[name="search-options"][value="3"]').should('not.be.checked')
                })
            })
        })
    })


    it(`Search "entity" -> 17 results`, () => {
        search("entity")
        assertSearchResultCount(17)
    })

    it(`Search "document" -> 6 results`, () => {
        search("document")
        assertSearchResultCount(6)
    })

    it(`Search "entity OR document" -> 23 results`, () => {
        search("entity OR document")
        assertSearchResultCount(23)
    })

    it(`Search "entity OR document OR qwerty" -> 23 results`, () => {
        search("entity OR document OR qwerty")
        assertSearchResultCount(23)
    })

    it(`Search "entity AND address" -> 4 results`, () => {
        search("entity AND address")
        assertSearchResultCount(4)
    })

    it(`Search "entity AND address AND qwerty" -> 0 results`, () => {
        search("entity AND address AND qwerty")
        assertSearchResultCount(0)
    })

    it(`Search "entity OR document AND qwerty" -> 17 results`, () => {
        search("entity OR document AND qwerty")
        assertSearchResultCount(17)
    })

    it(`Empty clauses ({} OR {}) -> 0 results`, () => {
        search("entity AND Never or document AND Never ")
        assertSearchResultCount(0)
    })

    it(`AND entity -> 17 results`, () => {
        search("AND entity ")
        assertSearchResultCount(17)
    })

    it(`OR entity -> 17 results`, () => {
        search("OR entity ")
        assertSearchResultCount(17)
    })

})

// Do WE want to test result when different options are select or is this already
