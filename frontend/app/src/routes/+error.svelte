<script lang="ts">
  import { page } from "$app/state";
  import { t } from "#lib/i18n";

  const notFound = $derived(page.status === 404);
  const titleKey = $derived(notFound ? "error.not-found.title" : "error.generic.title");
  const textKey = $derived(notFound ? "error.not-found.text" : "error.generic.text");
</script>

<svelte:head>
  <title>{t(titleKey)}</title>
</svelte:head>

<main>
  <h1>{t(titleKey)}</h1>
  <p>{t(textKey)}</p>
  <p><a href="/">{t("error.home")}</a></p>
</main>
