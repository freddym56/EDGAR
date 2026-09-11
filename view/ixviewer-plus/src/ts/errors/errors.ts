/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

export const Errors =
{

	createBsCloseBtn: (): HTMLElement => {
		const button = document.createElement('button');
		button.setAttribute('type', 'button');
		button.setAttribute('class', 'btn-close float-end');
		button.setAttribute('data-bs-dismiss', 'alert');
		button.setAttribute('aria-label', 'Close');
		return button;
	}
};
