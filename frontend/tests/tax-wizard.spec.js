import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
    await page.goto('/');

    // Step 0: Personal & Visa Details
    await page.getByLabel('Full Name').fill('John Doe');
    await page.getByLabel('SSN/ITIN').fill('123-45-6789');
    await page.getByLabel('Visa Type').selectOption('F1');
    await page.getByLabel('Country of Residence').fill('India');
    // Fill new fields
    await page.getByLabel('Date of Entry (First Arrival)').fill('2021-08-15');
    await page.getByLabel('Days in US (2025)').fill('365');
    await page.getByPlaceholder('Address').fill('123 Main St');
    await page.getByPlaceholder('City').fill('New York');
    await page.getByLabel('State', { exact: true }).selectOption('NY'); // Select by label 'State' might be ambiguous with 'State Income Tax' later, but on step 0 it should be fine. actually select keys off name usually or label.
    // The select has name="state", label "State".
    // Using getByRole('combobox', { name: 'State' }) might be safer if label alignment is an issue, but getByLabel is usually good.
    // Wait, there is a select for state.
    await page.getByPlaceholder('Zip').fill('10001');

    await page.getByRole('button', { name: 'Next' }).click();

    // Step 1: Income & Taxes
    await page.getByLabel('Wages (Box 1)').fill('50000');
    await page.getByLabel('Federal Withholding (Box 2)').fill('5000');
    await page.getByLabel('Social Security (Box 4)').fill('0');
    await page.getByLabel('Medicare (Box 6)').fill('0');

    await page.getByLabel('State Income Tax (Box 17)').fill('2000');
    await page.getByLabel('Charitable Contributions').fill('500');

    await page.getByRole('button', { name: 'Next' }).click();

    // Step 2: Direct Deposit
    await page.getByLabel('Routing Number').fill('123456789');
    await page.getByLabel('Account Number').fill('987654321');


    // Verify Preview section appears
    await expect(page.getByText('Review & Diagnostics')).toBeVisible();
    await expect(page.getByText('Taxable Income')).toBeVisible();

    // Verify Preview section appears
    await expect(page.getByText('1040nr Preview')).toBeVisible();

    // Click Submit (Download)
    // Note: Download might not work in headless without event listener, but we can check if the button is enabled.
    // The button text is "Download Official PDF"
    await expect(page.getByRole('button', { name: 'Download Official PDF' })).toBeEnabled();
});
