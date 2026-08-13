import {expect, test} from '@playwright/test';

test('technician completes grounded diagnosis and report flow', async ({page}) => {
  await page.goto('/');
  await expect(page.getByText('Intermittent thermal trip')).toBeVisible();

  await page.getByRole('button', {name: 'Run AI diagnosis', exact: true}).click();
  await expect(page.getByText('Restricted cooling airflow')).toBeVisible();

  await page.getByRole('button', {name: /Evidence/}).click();
  await expect(page.getByText('MAN-PMP-01-S4.2')).toBeVisible();

  await page.getByRole('button', {name: 'AI diagnosis', exact: true}).click();
  await page.getByLabel('I reviewed and approve this plan').check();
  await page.getByRole('button', {name: 'Generate service report'}).click();

  await expect(page.locator('pre')).toContainText('"report_id"');
  await expect(page.locator('pre')).toContainText('"approved": true');
});
