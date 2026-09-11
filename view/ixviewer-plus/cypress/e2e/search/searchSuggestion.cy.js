import { selectors } from "../../utils/selectors.mjs"

describe('Search recommendation box tests', () => {
    it('Search suggestion box should only appear when the search field is in focus', () => {
        cy.loadByAccessionNum('000080786323000002')
        cy.get(selectors.search).type('92101')
        cy.get(selectors.searchSuggestBox).should('be.visible').then(() => {
            cy.get('#fact-identifier-2').click()
            cy.get(selectors.searchSuggestBox).should('not.be.visible')
        })
    });

    it('More Facts should expand list', () => {
        cy.loadByAccessionNum('000143774923034166'); //nmex
        cy.get(selectors.search).type('000');
        cy.get('#suggestions > a:not(.d-none)').should('have.length', '3');
        cy.get('#moreFactsBtn').should('be.visible');
        cy.get('#moreFactsBtn').click();
        cy.get('#suggestions > a:not(.d-none)').should('have.length', '6');
        cy.get('#moreFactsBtn').should('not.be.visible');
    });

    it('Clicking suggestion should execute search and select fact', () => {
        cy.loadByAccessionNum('000143774923034166'); //nmex
        cy.get(selectors.searchHourglass).should("not.be.visible");
        cy.get(selectors.search).type('000');
        cy.get('#moreFactsBtn').click();
        cy.wait(300)
        cy.get('#suggestions > a:nth-child(4)').click();
        cy.hash().should('eq', '#fact-identifier-46');
        cy.get('#fact-identifier-46').should('have.attr', 'selected-fact', 'true');
        cy.get(selectors.factCountBadge).should('contain.text', '49'); // down from 226
    });

    describe('logical test', () => {
        beforeEach(() => {
            cy.loadByAccessionNum('000143774923034166').then(() => {
                // Uncheck "Include Fact Content" and "Include Fact Content"
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

        it(`Type "entity OR doc" -> Suggestions Appear`, () => {
            cy.get(selectors.search).type('entity or doc');
            cy.get(selectors.searchSuggestBox).should('be.visible')
        })

        it(`Type "entity AND doc" -> Suggestions Not Appear`, () => {
            cy.get(selectors.search).type('entity and doc');
            cy.get(selectors.searchSuggestBox).should('not.be.visible')
        })

        it(`Type "entity AND address" -> 4 Suggestions Not Appear`, () => {
            cy.get(selectors.search).type('entity AND address');
            cy.get(selectors.searchSuggestBox).should('be.visible')

            cy.get('#moreFactsBtn').should('be.visible');
            cy.get('#moreFactsBtn').click();

            cy.get('#suggestions > a:not(.d-none)').should('have.length', '4');
        })  
    })
})
