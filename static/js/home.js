// static/js/home.js

/**
 * Open the delete modal and populate all delete actions dynamically.
 *
 * Args:
 *   bookId (number): ID of the selected book.
 *   authorId (number): ID of the book's author.
 *   bookCount (number): Number of books the author has.
 *
 * Behavior:
 *   • Shows modal + overlay.
 *   • Wires "Delete single Book" to mode=book.
 *   • Shows "Delete Book & Author" ONLY if author has exactly 1 book.
 *   • Wires "Delete all Books and Author" to author delete route.
 */
function openDeleteModal(bookId, authorId, bookCount) {
  // Show modal + overlay
  document.getElementById("modal-overlay").style.display = "block";
  document.getElementById("delete-modal").style.display = "block";

  // Delete single book
  document.getElementById("delete-book-form").action =
    `/book/${bookId}/delete?mode=book`;

  // Delete book + author (only if last book)
  const bookAuthorForm = document.getElementById("delete-book-author-form");
  if (bookCount === 1) {
    bookAuthorForm.style.display = "block";
    bookAuthorForm.action =
      `/book/${bookId}/delete?mode=book_and_author`;
  } else {
    bookAuthorForm.style.display = "none";
  }

  // Delete author + all books
  document.getElementById("delete-author-form").action =
    `/author/${authorId}/delete`;
}

/**
 * Close the delete modal and hide overlay.
 */
function closeDeleteModal() {
  document.getElementById("modal-overlay").style.display = "none";
  document.getElementById("delete-modal").style.display = "none";
}
