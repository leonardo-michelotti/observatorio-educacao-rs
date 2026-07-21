const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

async function expectAccessible(page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

test("análise permite explorar os dados e abrir a tabela", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/Observatório da Educação/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("A distância aumenta");
  await expect(page.locator(".data-freshness")).toContainText("Dados disponíveis:");

  await expectAccessible(page);

  await page.getByRole("button", { name: "ver tabela" }).click();
  await expect(page.getByRole("button", { name: "ver gráfico" })).toBeVisible();
  await expect(page.locator("#ex-table table")).toBeVisible();
});

test("arquitetura documenta fontes e limites", async ({ page }) => {
  await page.goto("/arquitetura.html");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Arquitetura");
  await expect(page.getByText("Duas rotas de entrada", { exact: false })).toBeVisible();
  await expect(page.getByText("Limite de leitura", { exact: true })).toBeVisible();

  await expectAccessible(page);
});

test("navegação e explorador funcionam em tela móvel", async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 915 });
  await page.goto("/");

  await expect(page.getByRole("navigation", { name: "Navegação principal" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Taxa de aprovação" }).click();
  await expect(page.locator("#ex-title")).toContainText("Taxa de aprovação");
});
