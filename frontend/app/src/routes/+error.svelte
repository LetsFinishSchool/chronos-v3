<script lang="ts">
  import { t } from "#lib/i18n";
</script>

<svelte:head>
  <title>{t("error.not-found.title")}</title>
</svelte:head>

<main>
  <h1>{t("error.not-found.title")}</h1>
  <p>{t("error.not-found.text")}</p>
  <p><a href="/">{t("error.not-found.home")}</a></p>
</main>
