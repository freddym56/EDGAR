// import { filings } from '../../dataPlus/enrichedFilingsPlus.mjs'
import { getFilingsSample } from '../../dataPlus/filingsFunnel.js'
import { selectors } from "../../utils/selectors.mjs"

let filingsSample = getFilingsSample(Cypress.env);

/*
npx cypress run --spec 'cypress/e2e/inlineDocPagination/inlineDocPagination.cy.js'
*/


/*
filing http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/0001193125-23-248859/d555678dn6a.htm#
has style="page-break-after:always" and 319 breaks
*/

/*
2 instances 
filing http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/0001013762-23-000425/ea185980-6k_inspiratech.htm#
has 2 breaks
filing http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/0001013762-23-000425/ea185980ex99-1_inspiratech.htm#
has 17 breaks
*/

function distFromBtmOfViewportToBtmOfPage() {
    // Get the height of the viewport.
    const viewportHeight = window.innerHeight;
    // Get the offset of the bottom of the page from the top of the viewport.
    const pageBottomOffset = document.documentElement.scrollHeight - window.pageYOffset;
    // Calculate the distance from the bottom of the viewport to the bottom of the page.
    const distToBtmOfPage= pageBottomOffset - viewportHeight;
    return distToBtmOfPage;
}

// TODO: click event seems to be applying multiple times, but only in cypress....
describe(`Pagination Controls for 'pages' in Inline Doc`, () => {
/*
    // TODO: Need to test [style*="page-break-after"] case
    it.skip('[style*="page-break-after"]', () => {
        // doesn't work.  Scrolling is really hard to test in cypress for some reason. Not worth fixing for now, but we can keep documenting test urls here and skipping them.
        if (Cypress.env('domain')) {
            cy.visitFiling(null, "0000051143-23-000021-xbrl", `ibm-20230630.htm#`);
            cy.onClickShouldScrollDown(selectors.goToNextInlinePage);
            cy.onClickShouldScrollUp(selectors.goToPrevInlinePage);
        }
    })
*/

/*
    // TODO: Need to test [style*="break-before"] case
    it.skip('[style*="break-before"]', () => {

    })

    it(`Next page should work`, () => {
        cy.loadByAccessionNum('000101376223000425')
        cy.onClickShouldScrollDown(selectors.goToNextInlinePage)
    })

    //This one is flaky - gotta come back and fix later
    it.skip(`Next page, then prev page should bring back to top`, () => {
        cy.loadByAccessionNum('000101376223000425');
        cy.onClickShouldScrollDown(selectors.goToNextInlinePage).then($viewerElem =>{
            cy.wait(3000)
            cy.get(selectors.goToPrevInlinePage).click().then($viewerElem => {
                cy.get('div[id="dynamic-xbrl-form"]').then($viewerElem => {
                    cy.expect($viewerElem.scrollTop()).to.equal(0)
                })
            })
        });
    })
*/

/*
    it.skip(`Should loop and click next max times`, () => {
        // this won't work; perhaps because the cypress iframe window needs the `overflow: hidden` property.
        cy.loadByAccessionNum('000101376223000425');
        cy.get('[id^="fact-identifier-"]');

        // how many element match the next page selector? // just 1, so stil not sure why next page seems to be clicked multiple times.
        cy.get(selectors.goToNextInlinePage).each((sel, ind, arr) => {
            cy.log('sel', sel)
            cy.log('arr', arr)
        })

        // each approach
        cy.get(`section[filing-url="ea185980ex99-1_inspiratech.htm"] [style*="break-before"]`).each(breakElem => {
            cy.wrap(breakElem).scrollIntoView()
            cy.scrollTo(0, -500)
            cy.onClickShouldScrollDownFlat('@breakCollection', selectors.goToNextInlinePage)
        })

        // recursion approach
        cy.get(`section[filing-url="ea185980ex99-1_inspiratech.htm"] [style*="break-before"]`).as('breakCollection')
        cy.log('1 @breakCollection', '@breakCollection', ('@breakCollection').length)
    })

*/

/*
    // fails on command line (AssertionError: expected 8 to equal 0), but works on cypress gui.
    it.skip(`Go to bottom and top of page should work`, () => {
        cy.visitFiling(null, "0001013762-23-000425", `ea185980ex99-1_inspiratech.htm`)

        // wait for facts to show up
        cy.get('[id^="fact-identifier-"]').first();

        // bottom
        cy.get(selectors.goToBtnOfDoc).click();
        cy.expect(distFromBtmOfViewportToBtmOfPage()).to.equal(0)
        cy.get(selectors.goToNextInlinePage).click();
        cy.expect(distFromBtmOfViewportToBtmOfPage()).to.equal(0)
        
        // top
        cy.get(selectors.goToTopOfDoc).click();
        cy.get('div[id="dynamic-xbrl-form"]').then($viewerElem => {
            cy.expect($viewerElem.scrollTop()).to.equal(0)
        })
        // feature works but test doesn't; likely because the cypress iframe window needs the 'overflow: hidden;' property
        // .then(() => {
        //     cy.get(selectors.goToPrevInlinePage).click();
        //     cy.get('div[id="dynamic-xbrl-form"]').then($viewerElem => {
        //         cy.expect($viewerElem.scrollTop()).to.equal(0)
        //     })
        // })
    })
*/

    it('pagination should not show for docs that do not have page breaks', () => {
        cy.visit('/Archives/edgar/data/1415744/000143774923034166/nmex20231031_10q.htm');
        cy.get(selectors.docPagination).should('not.exist');
    })
    
    it('pagination should show for docs that have pages', () => {
        cy.visit('/Archives/edgar/data/1837493/000101376223000425/ea185980ex99-1_inspiratech.htm');
        cy.get(selectors.docPagination).should('exist');
        cy.get(selectors.docPagination).should('not.have.class', 'd-none');
    })
})
