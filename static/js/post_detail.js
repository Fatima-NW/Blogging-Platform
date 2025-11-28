/**  This script handles the interactive features of the post detail page

 Features:
- Reply form prefilled with @username with Cancel and Reply options
- Toggle like/unlike button on posts
- Dynamic like count update via AJAX
- Edit comment functionality with Save and Cancel
- @username search and dropdown for mentions
 */


document.addEventListener("DOMContentLoaded", function() {

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie("csrftoken");



    // ------------------------- For Replies -------------------------
    document.querySelectorAll(".reply-btn").forEach(button => {
        button.addEventListener("click", function () {
            let commentId = this.dataset.commentId;
            let username = this.dataset.username;

            // Hide all other reply forms first
            document.querySelectorAll(".reply-form").forEach(f => f.style.display = "none");

            // Show selected reply form and prefill mention
            let form = document.getElementById("reply-form-" + commentId);
            form.style.display = "block";

            let textarea = form.querySelector("textarea");
            textarea.value = "@" + username + " ";
            textarea.focus();
        });
    });

    document.querySelectorAll(".reply-form .cancel-reply-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const form = this.closest(".reply-form");
            if (form) form.style.display = "none";
        });
    });



    // ------------------------- For Likes -------------------------
    const likeBtn = document.getElementById("like-btn");
    if (!likeBtn) return;

    likeBtn.addEventListener("click", function () {
        const postId = this.dataset.postId;
        console.log("Like button clicked for post:", postId);

        fetch(`/posts/${postId}/like/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
        })
        .then(response => {
            console.log("Fetch response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Server response JSON:", data);

            // Update button
            const icon = likeBtn.querySelector("img");
            if (data.liked) {
                icon.src = "/static/img/liked.png";
                likeBtn.classList.remove("unliked-btn");
                likeBtn.classList.add("liked-btn");
            } else {
                icon.src = "/static/img/like.png";
                likeBtn.classList.remove("liked-btn");
                likeBtn.classList.add("unliked-btn");
            }

            // Update like count
            document.getElementById("like-count").textContent =
                data.like_count + " like" + (data.like_count === 1 ? "" : "s");
        })
        .catch(error => console.error("Fetch error:", error));
    });

    

    // ------------------------- For Updating Comments -------------------------
    let activeEditor = null;  

    // Open editor on "Edit" click
    document.body.addEventListener("click", function (e) {
        const el = e.target.closest && e.target.closest(".edit-comment");
        if (!el) return;

        e.preventDefault();
        const commentId = el.dataset.commentId;
        const commentWrapper = el.closest(".border-start") || el.closest(".border");

        if (!commentWrapper) return;

        const contentP = commentWrapper.querySelector("p.mb-1, p:not(:has(.edit-textarea))");
        if (!contentP) return;

        // Restore any previously open editor
        if (activeEditor && activeEditor !== contentP) {
            activeEditor.innerHTML = activeEditor.dataset.original;
            activeEditor = null;
        }

        // Replace text with textarea + buttons
        contentP.dataset.original = contentP.innerHTML;
        activeEditor = contentP;
        const originalText = contentP.textContent.trim();

        contentP.innerHTML = `
            <textarea class="form-control edit-textarea mb-2" rows="2">${escapeHtml(originalText)}</textarea>
            <div class="d-flex gap-2">
                <button class="btn btn-sm save-edit-btn" data-comment-id="${commentId}">Save</button>
                <button class="btn btn-sm cancel-edit-btn">Cancel</button>
            </div>
        `;

        const textarea = contentP.querySelector(".edit-textarea");
        attachMentionListener(textarea);
        textarea.focus();
    });

    // Handle Save and Cancel actions
    document.body.addEventListener("click", function (e) {
        // Cancel edit
        if (e.target.closest && e.target.closest(".cancel-edit-btn")) {
            const container = e.target.closest(".card, .border-start");
            if (!container) return;
            const contentP = container.querySelector("p.mb-1, p");
            if (!contentP) return;
            contentP.innerHTML = contentP.dataset.original || contentP.textContent;
            activeEditor = null;
            return;
        }

        // Save edit
        const saveBtn = e.target.closest && e.target.closest(".save-edit-btn");
        if (!saveBtn) return;

        e.preventDefault();
        const commentId = saveBtn.dataset.commentId;
        const container = saveBtn.closest(".border-start") || saveBtn.closest(".mb-3");
        const contentP = container.querySelector("p:has(.edit-textarea)");
        const textarea = contentP ? contentP.querySelector(".edit-textarea") : null;
        const newContent = textarea ? textarea.value.trim() : "";

        if (!newContent) {
            alert("Comment cannot be empty.");
            return;
        }

        // AJAX update request
        fetch(`/posts/comment/${commentId}/edit/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            body: new URLSearchParams({ content: newContent }).toString()
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                contentP.innerHTML = escapeHtml(data.updated_content);
                activeEditor = null;
            } else {
                alert(data.error || "Failed to update comment.");
            }
        })
        .catch(() => alert("Network error while updating comment."));
    });

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }



    // ------------------------- @Username Search -------------------------
    let dropdown = document.createElement('ul');
    dropdown.classList.add('mention-dropdown');
    document.body.appendChild(dropdown);

    let activeTextarea = null;

    function attachMentionListener(textarea) {
        textarea.addEventListener('keyup', async (e) => {
            activeTextarea = textarea;
            const text = textarea.value;
            const match = text.match(/@(\w*)$/);

            if (match && match[1].length > 0) {
                const res = await fetch(`/api/users/search/?q=${match[1]}`);
                const usernames = await res.json();

                if (!usernames.length) {
                    dropdown.style.display = 'none';
                    return;
                }

                dropdown.innerHTML = usernames
                    .map(u => `<li class="mention-item">@${u}</li>`)
                    .join('');

                // Position dropdown relative to the textarea
                const rect = textarea.getBoundingClientRect();
                dropdown.style.top = `${rect.bottom + window.scrollY}px`;
                dropdown.style.left = `${rect.left + window.scrollX}px`;
                dropdown.style.width = `${rect.width}px`;
                dropdown.style.display = 'block';
            } else {
                dropdown.style.display = 'none';
            }
        });
    }

    document.querySelectorAll('textarea[name="content"]').forEach(attachMentionListener);

    // Click on dropdown item
    dropdown.addEventListener('click', (e) => {
        if (e.target.classList.contains('mention-item') && activeTextarea) {
            const selected = e.target.innerText;
            activeTextarea.value = activeTextarea.value.replace(/@\w*$/, selected + ' ');
            dropdown.style.display = 'none';
            activeTextarea.focus();
        }
    });

    // Click outside hides dropdown
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && ![...document.querySelectorAll('textarea[name="content"]')].includes(e.target)) {
            dropdown.style.display = 'none';
        }
    });


});