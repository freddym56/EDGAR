/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

import { ConstantsFunctions } from "../constants/functions";
import { FactsGeneral } from "../facts/general";
import { UserFiltersState } from "../user-filters/state";
import { actionKeyHandler } from "../helpers/utils";
import { callSearch } from "../flex-search/search-worker-interface";
import { searchUiUpdate, showSearchingHourglass } from "../flex-search/flex-search-ui";
// import { buildArrowKeyListenerForElems } from "../helpers/utils"; // WIP

export const Search = {

  clear: () => {
    ConstantsFunctions.emptyHTMLByID('suggestions');
    (document.getElementById('global-search') as HTMLInputElement).value = '';
    UserFiltersState.setUserSearch({});
    // FlexSearch.searchFacts({});
    callSearch({}).then(searchResults => {
      if (searchResults === undefined) return
      searchUiUpdate(searchResults);
    })
  },

  closeSuggestions: () => {
    ConstantsFunctions.emptyHTMLByID('suggestions');
  },

  getSearchQuery: () => {
    const valueToSearchFor = (document.getElementById('global-search') as HTMLInputElement).value;

    const options = document.querySelectorAll('[name="search-options"]');
    let optionsArray = Array.prototype.slice.call(options);
    optionsArray = optionsArray.map((current) => {
      if (current['checked']) {
        return Number.parseInt(current['value']);
      }
    }).filter(Boolean);

    const { clauses } = Search.normalizeValueToSearchFor(valueToSearchFor)
    // Searching "cat and dog or mouse and sheep" -> clauses = [["cat", "dog"],["mouse","sheep"]]
    // ["cat", "dog"]     => clause 1
    // ["mouse","sheep"]  => clause 2
    const query = {
      clauses,
      'options': optionsArray
    };

    return query

  },

  submit: () => {
    // 1 => Include Fact Name
    // 2 => Include Fact Content
    // 3 => Include Labels
    // 4 => Include Definitions
    // 5 => Include Dimensions
    // 6 => Include References
    showSearchingHourglass();
    ConstantsFunctions.emptyHTMLByID('suggestions');
    // let valueToSearchFor = (document.getElementById('global-search') as HTMLInputElement).value;
    // here we sanitize the users input to account for Regex patterns

    const query = Search.getSearchQuery();
    UserFiltersState.setUserSearch(query);

    callSearch(query).then(searchResults => {
      if (searchResults === undefined) return
      searchUiUpdate(searchResults);
    })
  },

  normalizeValueToSearchFor: (input: string) => {
    const normalized = input.replaceAll(/\band\b/gi, ' & ').replaceAll(/\bor\b/gi, ' | ').toLowerCase();

    const clauses = normalized
      .split('|')
      .map(clause => clause.split('&').map(t => t.trim()).filter(Boolean))
      .filter(clause => clause.length > 0)

    return { clauses }
  },


  suggestions: () => {
    const smallSetSize = 3;
    const lrgSetSize = 6;
    let valueToSearchFor = (document.getElementById('global-search') as HTMLInputElement).value;
    const search = document.getElementById('global-search');
    ConstantsFunctions.emptyHTMLByID('suggestions');
    if (valueToSearchFor.length > 1 && document.activeElement === search) {
      const query = Search.getSearchQuery();

      const suggestionsUl = document.getElementById('suggestions') as HTMLElement;

      const populateSuggestionsUi = (results: string[]) => {
        results?.slice(0, lrgSetSize).forEach((current: string, index) => {
          const hidden = index >= smallSetSize;
          const factListMember = FactsGeneral.renderFactElem(current, hidden);
          suggestionsUl.append(factListMember);
        });
      }

      const addMoreFactsButton = (results: string[]) => {
        // More Facts Button
        if (results && results.length > smallSetSize) {
          const moreFactsLi = document.createElement('li');
          moreFactsLi.classList.add('hover-dim', 'list-group-item', 'not-numbered', 'd-flex', 'justify-content-between', 'align-items-start');

          const moreFactsDiv = document.createElement('div');
          moreFactsDiv.setAttribute('id', 'moreFactsBtn');
          moreFactsDiv.classList.add('ms-2', 'me-auto');

          const title = document.createTextNode(`More Facts`);
          moreFactsDiv.append(title);
          moreFactsLi.append(moreFactsDiv);
          suggestionsUl.append(moreFactsLi);

          // action
          moreFactsLi.addEventListener('click', (e) => {
            e.stopPropagation(); // so it doesn't close suggestions
            const hiddenSuggestions = suggestionsUl.querySelectorAll('#suggestions a.d-none');
            hiddenSuggestions.forEach(hiddenFactResult => {
              hiddenFactResult.classList.remove('d-none');
            })
            moreFactsLi.classList.add('d-none')
            suggestionsUl.style.maxHeight = '85vh';
          })
        }
      }

      callSearch(query).then(searchResults => {
        const searchResultsArray: string[] = Array.from(searchResults)
        populateSuggestionsUi(searchResultsArray);
        addMoreFactsButton(searchResultsArray);
      })

      document.getElementById('global-search-form')?.append(suggestionsUl);

      window.setTimeout(() => {
        // submit search upon clicking suggestion
        const suggestionElems = document.querySelectorAll('#suggestions > a');
        suggestionElems?.forEach(((suggestionElem) => {
          suggestionElem.addEventListener('click', Search.submit);
          suggestionElem.addEventListener('keyup', (event) => {
            if (!actionKeyHandler(event as KeyboardEvent)) return;
            Search.submit()
          })
        }))
      }, 200)

      // wip adding arrow key functionality amongst suggestions
      // const moreFactsBtn = document.getElementById('moreFactsBtn');
      // const searchSuggestionElems = Array.from(document.querySelectorAll('[id="suggestions"] > a'));
      // const suggestionElems = [search, ...searchSuggestionElems, moreFactsBtn]
      // buildArrowKeyListenerForElems(suggestionElems)
    }
  },

  suggestionsEmpty: () => {
    ConstantsFunctions.emptyHTMLByID('suggestions')
  },

}
