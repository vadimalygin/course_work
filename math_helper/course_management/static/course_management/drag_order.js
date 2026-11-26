function updateMoveButtons(list) {
  const items = Array.from(list.querySelectorAll("[data-sortable-item]"));
  items.forEach((item, index) => {
    item.querySelector('[data-move="up"]').disabled = index === 0;
    item.querySelector('[data-move="down"]').disabled = index === items.length - 1;
  });
}

document.querySelectorAll("[data-sortable-list]").forEach((list) => {
  updateMoveButtons(list);

  let draggedItem = null;
  let pointerId = null;

  list.addEventListener("pointerdown", (event) => {
    const handle = event.target.closest("[data-sortable-handle]");
    if (!handle || event.button !== 0 || !event.isPrimary) return;

    draggedItem = handle.closest("[data-sortable-item]");
    if (!draggedItem) return;

    pointerId = event.pointerId;
    handle.setPointerCapture(pointerId);
    draggedItem.classList.add("dragging", "opacity-50");
    event.preventDefault();
  });

  list.addEventListener("pointermove", (event) => {
    if (!draggedItem || event.pointerId !== pointerId) return;

    const target = document.elementFromPoint(event.clientX, event.clientY)
      ?.closest("[data-sortable-item]");
    list.querySelectorAll(".drop-target").forEach((item) => {
      item.classList.remove("drop-target", "border-warning", "bg-subtle-warning");
    });
    if (!target || target === draggedItem || !list.contains(target)) return;

    target.classList.add("drop-target", "border-warning", "bg-subtle-warning");
    const shouldInsertBefore = event.clientY < target.getBoundingClientRect().top + target.offsetHeight / 2;
    list.insertBefore(draggedItem, shouldInsertBefore ? target : target.nextElementSibling);
  });

  const finishDrag = (event) => {
    if (!draggedItem || event.pointerId !== pointerId) return;

    list.querySelectorAll(".dragging, .drop-target").forEach((item) => {
      item.classList.remove(
        "dragging",
        "drop-target",
        "opacity-50",
        "border-warning",
        "bg-subtle-warning",
      );
    });
    draggedItem = null;
    pointerId = null;
    updateMoveButtons(list);
  };

  list.addEventListener("pointerup", finishDrag);
  list.addEventListener("pointercancel", finishDrag);

  list.addEventListener("click", (event) => {
    const button = event.target.closest("[data-move]");
    if (!button) return;

    const item = button.closest("[data-sortable-item]");
    const neighbor = button.dataset.move === "up"
      ? item.previousElementSibling
      : item.nextElementSibling;
    if (!neighbor) return;

    if (button.dataset.move === "up") {
      list.insertBefore(item, neighbor);
    } else {
      list.insertBefore(neighbor, item);
    }
    updateMoveButtons(list);
  });
});
