import { randomUUID } from "node:crypto";
import { expect, request, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import type { RecommendationRun } from "../src/shared/api/types";

const password = "Passw0rd123";

const profile = {
  programmes: ["talent"],
  birth_date: "2003-05-10",
  english_level: "B2",
  study: { status: "bachelor", course: 3, specialty_text: "Маркетинг" },
  other_languages: ["ru"],
  work_experience: "none",
  spheres: ["marketing", "sales"],
  desired_countries: ["TR"],
  duration: { min_weeks: 6, max_weeks: 12 },
  start_window: "asap",
  financial: { willing_to_pay: true, max_budget_eur: 500, needs_stipend: false },
  motivation_text: "Синтетическая анкета для браузерного теста",
};

test.describe("Браузерный тест: сохранение рекомендации в избранном", () => {
  test("Добавление рекомендованной стажировки в избранное с сохранением после перезагрузки.", async ({
    page,
  }) => {
    const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173";
    const email = `qa_${randomUUID().replaceAll("-", "").slice(0, 12)}@example.com`;
    const setupApi = await request.newContext({ baseURL });
    let userApi: APIRequestContext | undefined;

    try {
      const registerResponse = await setupApi.post("/api/v1/auth/register", {
        data: { email, password },
      });
      expect(registerResponse.status()).toBe(200);
      const auth = (await registerResponse.json()) as { access_token: string };
      expect(auth.access_token).toBeTruthy();

      userApi = await request.newContext({
        baseURL,
        extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` },
      });

      const consentSchemaResponse = await setupApi.get("/api/v1/meta/consents");
      expect(consentSchemaResponse.status()).toBe(200);
      const consentSchema = (await consentSchemaResponse.json()) as {
        consents: Array<{ kind: string; version: string }>;
      };
      const consent = consentSchema.consents.find((item) => item.kind === "pd_processing");
      if (!consent) throw new Error("The required personal-data consent is not configured.");

      const consentResponse = await userApi.post("/api/v1/me/consents", {
        data: { kind: consent.kind, version: consent.version },
      });
      expect(consentResponse.status()).toBe(204);

      const profileResponse = await userApi.put("/api/v1/profiles/me", { data: profile });
      expect(profileResponse.status()).toBe(200);

      const recommendationResponse = await userApi.post("/api/v1/recommendations", {
        data: { mode: "sync", limit_per_programme: 10 },
        headers: { "Idempotency-Key": randomUUID() },
      });
      expect(recommendationResponse.status()).toBe(200);
      const run = (await recommendationResponse.json()) as RecommendationRun;
      expect(run.state).toBe("succeeded");

      const activeGroup = run.groups.find(
        (group) => group.programme_kind === run.programme_prior[0],
      );
      if (!activeGroup) throw new Error("The recommendation run has no active programme group.");
      const visibleItems = activeGroup.items.filter((item) => !item.hidden && !item.liked);
      const target = visibleItems[0];
      if (!target) throw new Error("The prepared profile has no visible recommendations.");
      const title = target.opportunity.title;
      const opportunityId = target.opportunity.opportunity_id;

      // 1. Open the prepared recommendation list in the test candidate's authenticated session.
      await page.goto("/login");
      await page.getByRole("textbox", { name: "Email" }).fill(email);
      await page.getByRole("textbox", { name: /^Пароль/ }).fill(password);
      await page.getByRole("button", { name: "Войти", exact: true }).click();
      await expect(page).toHaveURL(/\/app$/);
      await page.goto("/results");
      await expect(page.getByRole("heading", { name: "Рекомендации", exact: true })).toBeVisible();

      // 2. Record the selected opportunity ID from its details URL, then return to recommendations.
      const recommendationCard = page
        .getByRole("article")
        .filter({ has: page.getByRole("heading", { level: 3, name: title, exact: true }) })
        .first();
      await expect(recommendationCard).toBeVisible();
      await recommendationCard.getByRole("button", { name: "Подробнее", exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`/opportunity/${opportunityId}$`));
      await expect(page.getByRole("heading", { level: 1, name: title, exact: true })).toBeVisible();
      await page.goBack();
      await expect(page).toHaveURL(/\/results$/);

      // 3. Add the selected recommendation to favorites.
      const selectedCard = page
        .getByRole("article")
        .filter({ has: page.getByRole("heading", { level: 3, name: title, exact: true }) })
        .first();
      const toastVisible = expect(
        page.getByRole("status").filter({ hasText: "Добавлено в избранное" }),
      ).toBeVisible();
      const feedbackResponse = page.waitForResponse((response) => {
        const url = new URL(response.url());
        const body = response.request().postDataJSON() as { signal?: string } | null;
        return (
          url.pathname === "/api/v1/feedback" &&
          response.request().method() === "POST" &&
          body?.signal === "liked"
        );
      });
      await selectedCard.getByRole("button", { name: "Подходит", exact: true }).click();
      expect((await feedbackResponse).status()).toBe(204);
      await toastVisible;
      await expect(
        selectedCard.getByRole("button", { name: "В избранном", exact: true }),
      ).toBeDisabled();

      // 4. Open the favorites page through the profile navigation.
      await page.getByRole("link", { name: "Профиль", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Профиль", exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Избранное", exact: true }).click();
      await expect(page).toHaveURL(/\/profile\/favorites$/);
      await expect(page.getByRole("tab", { name: "Избранное", exact: true })).toHaveAttribute(
        "aria-selected",
        "true",
      );

      // 5. Reload favorites and confirm the exact opportunity is still listed.
      await page.reload();
      await expect(page.getByRole("heading", { name: "Избранное", exact: true })).toBeVisible();
      const favoriteCards = page
        .getByRole("article")
        .filter({ has: page.getByRole("heading", { level: 3, name: title, exact: true }) });
      await expect(favoriteCards.first()).toBeVisible();
      const favoriteCount = await favoriteCards.count();

      // 6. Confirm the card after reload resolves to the same opportunity ID.
      let foundSameOpportunity = false;
      for (let index = 0; index < favoriteCount; index += 1) {
        const favoriteCard = favoriteCards.nth(index);
        await expect(favoriteCard).toContainText(
          `${target.opportunity.place.country_name} · ${target.opportunity.place.lc_name}`,
        );
        await favoriteCard.getByRole("button", { name: "Подробнее", exact: true }).click();
        await expect(page).toHaveURL(/\/opportunity\/\d+$/);
        if (Number(new URL(page.url()).pathname.split("/").at(-1)) === opportunityId) {
          await expect(
            page.getByRole("heading", { level: 1, name: title, exact: true }),
          ).toBeVisible();
          foundSameOpportunity = true;
          break;
        }
        await page.goBack();
        await expect(page).toHaveURL(/\/profile\/favorites$/);
      }
      expect(foundSameOpportunity).toBe(true);
    } finally {
      if (userApi) {
        const deleteResponse = await userApi.delete("/api/v1/me");
        expect(deleteResponse.status()).toBe(204);
        await userApi.dispose();
      }
      await setupApi.dispose();
    }
  });
});
