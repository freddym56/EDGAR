import { selectors } from "./selectors.mjs"
export const search = (query) => {
    /**
     * Performs a search action using the global search input.
     *  - Clears the existing value in the search field
     *  - Submits the search with provided query
     *
     * @param {string} query - The search text to enter into the search field.
     */
    cy.get(selectors.search).clear().type(query)
    cy.get(selectors.search).type('{enter}')

    cy.get(selectors.searchHourglass).should('not.be.visible')
}

export const assertSearchResultCount = (n) => {
    /**
     * Asserts that the displayed search result count matches the expected value.
     *
     * @param {number} n - The expected number of search results.
     */

    cy.get(selectors.factCountBadge).should('have.text', `${n}`)
}