<script lang="ts">
  import { onMount } from "svelte";

  let { children } = $props();

  // Die Ladehülle aus app.html bleibt sonst neben der gemounteten Seite stehen.
  onMount(() => document.getElementById("shell")?.remove());
</script>

{@render children()}
