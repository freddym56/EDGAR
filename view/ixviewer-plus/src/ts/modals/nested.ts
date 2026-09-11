/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */
import { ConstantsFunctions } from "../constants/functions";
import { FactMap } from "../facts/map";


export const ModalsNested = {

	currentSlide: 0,

	carouselInformation: [{
		'dialog-title': 'Attributes'
	}, {
		'dialog-title': 'Labels'
	}, {
		'dialog-title': 'References'
	}, {
		'dialog-title': 'Calculation'
	}],

	dynamicallyFindContinuedFacts: (element: HTMLElement | null, elementsInArray: HTMLElement[]): HTMLElement[] =>
	{
		if (element)
		{
			elementsInArray.push(element);
			const continuedId = element.getAttribute('continuedat');

			if (continuedId)
			{
				const continuedElement = document.querySelector<HTMLElement>(`#dynamic-xbrl-form [id="${continuedId}"]`);
				return ModalsNested.dynamicallyFindContinuedFacts(continuedElement, elementsInArray);
			}
		}
		
		return elementsInArray;
	},

	getAllElementIDs: [] as Element[],
	getAllNestedFacts: (element: HTMLElement) => {
		//assume `element` is the "main" fact
		const getContinuedNestedElemIDs = (element: HTMLElement) => {
			if (element?.getAttribute('continued-main-fact') !== 'true') {
				console.warn("Not a parent fact!");
				const nestedFacts = Array.from(element.querySelectorAll('[id^="fact-identifier-"]')) as Array<HTMLElement>;
				ModalsNested.getAllElementIDs = [element, ...nestedFacts];
				return;
			}

			const nestedFacts = element.querySelectorAll('[id^="fact-identifier-"]');
			const continuedNestedFacts = ModalsNested.getOnlyContinuedFacts(element as HTMLElement, [])
				.flatMap((el: Element) => Array.from(el.querySelectorAll('[id^="fact-identifier-"]')));

			ModalsNested.getAllElementIDs = [element, ...nestedFacts, ...continuedNestedFacts];
		}

		if (element.getAttribute('continued-main-fact') === "true") {
			getContinuedNestedElemIDs(element);
		}
		else if (element.getAttribute("continued-main-fact-id")) {
			const parentId = element.getAttribute("continued-main-fact-id") || "";
			const parent = document.getElementById(parentId)!;
			getContinuedNestedElemIDs(parent);
		} else {
			ModalsNested.getAllElementIDs = [element, ...element.querySelectorAll('[id^="fact-identifier-"]')];
		}
	},
	
	getOnlyContinuedFacts: (element: Element, continuedElementsArray: Element[]): Element[] =>
	{
		const continuedId = element.getAttribute("continuedat");
		const continuedElement = document.querySelector(`#dynamic-xbrl-form [id="${continuedId}"]`);

		if (continuedElement)
		{
			continuedElementsArray.push(continuedElement);
			return ModalsNested.getOnlyContinuedFacts(continuedElement, continuedElementsArray);
		}

		return continuedElementsArray;
	},

	getElementById: (id: string): HTMLElement | HTMLElement[] | null =>
	{
		const element = document.querySelector<HTMLElement>(`#dynamic-xbrl-form [id="${id}"]`);
		if (element?.getAttribute('continued-main-fact') === 'true')
		{
			return ModalsNested.dynamicallyFindContinuedFacts(element, []);
		}

		return element;
	},

	createLabelCarousel: () => {
		const carousel = document.querySelector('#modal-fact-nested-label-carousel');
		if (carousel == null) return;

		// reset 
		carousel.innerHTML = "";

		// make "Nested Facts 1/18" label for modal title
		// create numator part
		const titleCarousel = document.createDocumentFragment();
		const currentFactNumSpan = document.createElement('span');
		const dialogTitle = document.createTextNode(`1`);
		currentFactNumSpan.appendChild(dialogTitle);
		document.getElementById('nested-page')?.firstElementChild?.replaceWith(currentFactNumSpan);
		
		// create denominator part
		const span1 = document.createElement('span');
		const dialogTitle1 = document.createTextNode(ModalsNested.getAllElementIDs.length.toString());
		span1.appendChild(dialogTitle1);
		document.getElementById('nested-count')?.firstElementChild?.replaceWith(span1);

		ModalsNested.getAllElementIDs.forEach((current) => {
			const factID = current.getAttribute('continued-main-fact-id') ? current.getAttribute('continued-main-fact-id') : current.getAttribute('id');
			const factInfo = FactMap.getByID(factID || "");

			const nestedFactName = ConstantsFunctions.getFactLabel(factInfo?.labels || []);

			const divTitleElement = document.createElement('div');
			divTitleElement.setAttribute('class', 'carousel-item nested-carousel');

			const divTitleNestedElement = document.createElement('div');
			divTitleNestedElement.setAttribute('class', 'carousel-content');

			const pTitleElement = document.createElement('p');
			pTitleElement.setAttribute('class', 'text-center font-weight-bold');
			const conceptNameContent = document.createTextNode(nestedFactName as string);
			pTitleElement.appendChild(conceptNameContent);
			divTitleNestedElement.appendChild(pTitleElement);
			divTitleElement.appendChild(divTitleNestedElement);
			titleCarousel.appendChild(divTitleElement);
		});

		carousel.appendChild(titleCarousel);
		carousel.querySelector('.carousel-item')?.classList.add('active');
	},

	createContentCarousel: (index: number) => {
		const element = ModalsNested.getElementById((ModalsNested.getAllElementIDs[index].id));
		ModalsNested.carouselData(element);
	},

	nestedClickEvent: (event: Event, element: HTMLElement) => {
		if (event instanceof KeyboardEvent && !(event.key === 'Enter' || event.key === 'Space'))
			return;

		event.preventDefault();
		event.stopPropagation();

	
		// we empty the ID Array
		ModalsNested.getAllElementIDs = [];
		// we load the ID Array
		ModalsNested.getAllNestedFacts(element);
	},


};