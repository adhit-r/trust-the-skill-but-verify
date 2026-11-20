document.addEventListener("DOMContentLoaded", () => {
  const rows = document.querySelectorAll("[data-ticket]");
  rows.forEach((row) => row.classList.add("ready"));
});
