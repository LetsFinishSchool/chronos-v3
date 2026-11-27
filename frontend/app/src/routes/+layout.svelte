<script lang="ts">
  import { onMount } from "svelte";
  import Router from "#lib/router/Router.svelte";

  let { children } = $props();

  // Die Ladehülle aus app.html bleibt sonst neben der gemounteten Seite stehen.
  onMount(() => document.getElementById("shell")?.remove());
</script>

<Router />
{@render children()}
