<script lang="ts">
  import { afterNavigate } from "$app/navigation";
  import { tick } from "svelte";

  let announcement = $state("");

  afterNavigate(async (navigation) => {
    // Beim ersten Laden gibt es keinen Seitenwechsel, den man ansagen müsste.
    if (navigation.type === "enter") return;
    // Erst nach dem Rendern der neuen Seite stehen deren h1 und Titel fest.
    await tick();
    const heading = document.querySelector("h1");
    if (heading) {
      if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
      heading.focus();
    }
    announcement = document.title;
  });
</script>

<div
  aria-live="polite"
  role="status"
  style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap;"
>
  {announcement}
</div>
