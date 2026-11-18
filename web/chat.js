/*
 * chat.js - Task 2.2
 *
 * The chat widget. It sends a visitor's question to the backend's /chat
 * endpoint and shows the answer, with the documents it came from.
 *
 * Safety rule for this file: text from the model is NEVER inserted as HTML.
 * Every reply is built with createElement and textContent, so a reply that
 * happened to contain <script> or <img onerror=...> is shown as harmless text.
 */

(function () {
  "use strict";

  // Where the backend lives. Stage 3 replaces this with the Hugging Face
  // address. A page can override it by setting window.BELLA_API_URL before
  // loading this file.
  var API_URL = window.BELLA_API_URL || "http://127.0.0.1:8000";

  // Must match MAX_QUESTION_CHARS in backend/main.py.
  var MAX_CHARS = 1000;

  var SUGGESTIONS = [
    "What are your fees for buying a house?",
    "Show me apartments for rent in Islamabad",
    "How do I book a viewing?"
  ];

  // -------------------------------------------------------------------------
  // Build the widget
  // -------------------------------------------------------------------------

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        node.setAttribute(key, attrs[key]);
      });
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  var launcher = el("button", {
    type: "button",
    class: "chat-launcher",
    "aria-expanded": "false",
    "aria-controls": "chat-panel"
  });
  // The robot is decoration; the button's name comes from the text label.
  var launcherBot = el("span", { class: "chat-bot", "aria-hidden": "true" });
  launcher.appendChild(launcherBot);
  launcher.appendChild(el("span", { class: "chat-launcher-label" }, "Ask a question"));

  var panel = el("section", {
    id: "chat-panel",
    class: "chat-panel",
    role: "dialog",
    "aria-label": "Bella Real Estate assistant",
    hidden: ""
  });

  var header = el("div", { class: "chat-header" });
  var headerBot = el("span", { class: "chat-bot chat-bot-header", "aria-hidden": "true" });
  var title = el("h2", { class: "chat-title" }, "Bella assistant");
  var titleWrap = el("div", { class: "chat-title-wrap" });
  titleWrap.appendChild(headerBot);
  titleWrap.appendChild(title);
  var closeButton = el("button", {
    type: "button",
    class: "chat-close",
    "aria-label": "Close chat"
  }, "×");
  header.appendChild(titleWrap);
  header.appendChild(closeButton);

  // aria-live makes screen readers announce new replies as they arrive.
  var log = el("div", { class: "chat-log", "aria-live": "polite" });

  var form = el("form", { class: "chat-form" });
  var label = el("label", { for: "chat-input", class: "visually-hidden" },
    "Your question");
  var input = el("textarea", {
    id: "chat-input",
    class: "chat-input",
    rows: "2",
    maxlength: String(MAX_CHARS),
    placeholder: "Ask about a property, fees or viewings"
  });
  var sendButton = el("button", { type: "submit", class: "chat-send" }, "Send");
  form.appendChild(label);
  form.appendChild(input);
  form.appendChild(sendButton);

  var note = el("p", { class: "chat-note" },
    "Answers come only from Bella Real Estate's own documents. " +
    "This is a demo with a fictional company.");

  panel.appendChild(header);
  panel.appendChild(log);
  // FR-07: a way to reach a person, always visible above the input.
  var actions = el("div", { class: "chat-actions" });
  var handoffButton = el("button", { type: "button", class: "chat-handoff" },
    "Talk to a person");
  actions.appendChild(handoffButton);
  panel.appendChild(actions);
  panel.appendChild(form);
  panel.appendChild(note);

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  // -------------------------------------------------------------------------
  // The robot avatar
  //
  // Two copies of the same animation. On the launcher it loops, to draw the
  // eye to the one thing on the page that talks back. In the panel header it
  // stands still and moves only while an answer is being fetched, so the
  // motion means something. With reduced motion requested, neither moves.
  //
  // Everything here is optional. If the player (web/vendor/lottie_light.min.js)
  // or the animation (web/assets/robot.js) failed to load, the widget works
  // exactly as before, without the robot.
  // -------------------------------------------------------------------------

  var reduceMotion = !!(window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function makeRobot(container) {
    if (!window.lottie || !window.BELLA_ROBOT) return null;
    try {
      var animation = window.lottie.loadAnimation({
        container: container,
        renderer: "svg",
        loop: true,
        autoplay: false,
        // lottie-web modifies the data it is given, so each copy gets its own.
        animationData: JSON.parse(JSON.stringify(window.BELLA_ROBOT))
      });
      container.classList.add("chat-bot-ready");
      return animation;
    } catch (error) {
      return null;
    }
  }

  var launcherRobot = makeRobot(launcherBot);
  var headerRobot = makeRobot(headerBot);

  function rest(robot) { if (robot) robot.goToAndStop(0, true); }
  function animate(robot) {
    if (!robot) return;
    if (reduceMotion) rest(robot); else robot.play();
  }

  animate(launcherRobot);
  rest(headerRobot);

  // -------------------------------------------------------------------------
  // Turning a reply into page elements, safely
  // -------------------------------------------------------------------------

  // Adds text to `parent`, turning **bold** into <strong>. Nothing else in
  // the text is interpreted.
  function appendInline(parent, text) {
    var parts = text.split(/\*\*(.+?)\*\*/g);
    parts.forEach(function (part, index) {
      if (!part) return;
      if (index % 2 === 1) {
        parent.appendChild(el("strong", null, part));
      } else {
        parent.appendChild(document.createTextNode(part));
      }
    });
  }

  // The model writes paragraphs and "- " bullet lists. Build those, and
  // treat everything else as plain text.
  function renderAnswer(container, answer) {
    var list = null;
    answer.split("\n").forEach(function (rawLine) {
      var line = rawLine.trim();
      if (!line) {
        list = null;
        return;
      }
      var bullet = line.match(/^[-*]\s+(.*)$/);
      if (bullet) {
        if (!list) {
          list = el("ul");
          container.appendChild(list);
        }
        var item = el("li");
        appendInline(item, bullet[1]);
        list.appendChild(item);
      } else {
        list = null;
        var paragraph = el("p");
        appendInline(paragraph, line);
        container.appendChild(paragraph);
      }
    });
  }

  function renderSources(container, sources, answer) {
    if (!sources || !sources.length) return;

    // The same heading can appear twice; show each once.
    var seen = {};
    var unique = sources.filter(function (source) {
      var key = source.source + "|" + source.heading;
      if (seen[key]) return false;
      seen[key] = true;
      return true;
    });

    // The search always returns 8 extracts, and the model is told to ignore
    // the ones that don't match. Listing all 8 as "sources" would show, say, a
    // Rawalpindi listing under an Islamabad answer. So when the answer names
    // reference codes, show only the extracts for those properties. When it
    // names none (fees, viewings), show everything, under an honest label.
    var codes = answer.match(/BRE-[SR]-\d+/g) || [];
    var shown = unique;
    var label = "Documents checked";
    if (codes.length) {
      var used = unique.filter(function (source) {
        return codes.some(function (code) {
          return source.heading.indexOf(code) === 0;
        });
      });
      if (used.length) {
        shown = used;
        label = "Sources";
      }
    }

    var details = el("details", { class: "chat-sources" });
    details.appendChild(el("summary", null,
      label + " (" + shown.length + ")"));
    var list = el("ul");
    shown.forEach(function (source) {
      var file = source.source.replace(/^data\//, "");
      list.appendChild(el("li", null, source.heading + " — " + file));
    });
    details.appendChild(list);
    container.appendChild(details);
  }

  // -------------------------------------------------------------------------
  // Messages
  // -------------------------------------------------------------------------

  function addMessage(who, text) {
    var bubble = el("div", { class: "chat-msg chat-msg-" + who });
    if (who === "bot") {
      renderAnswer(bubble, text);
    } else {
      bubble.textContent = text;
    }
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  function addSuggestions() {
    var wrap = el("div", { class: "chat-suggestions" });
    SUGGESTIONS.forEach(function (question) {
      var chip = el("button", { type: "button", class: "chat-chip" }, question);
      chip.addEventListener("click", function () {
        wrap.remove();
        send(question);
      });
      wrap.appendChild(chip);
    });
    log.appendChild(wrap);
  }

  addMessage("bot",
    "Hello. I can answer questions about Bella Real Estate's properties, " +
    "fees and viewings in Islamabad and Rawalpindi.");
  addSuggestions();

  // -------------------------------------------------------------------------
  // Talking to the backend
  // -------------------------------------------------------------------------

  var busy = false;
  var lastPropertyRef = "";

  function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    input.disabled = value;
    sendButton.textContent = value ? "Sending…" : "Send";
    if (value) animate(headerRobot); else rest(headerRobot);
  }

  // Errors say what happened and what to do, in the widget's own voice.
  function describeError(status, detail) {
    if (status === 0) {
      return "The assistant can't be reached. If you are running this " +
        "locally, start the backend with: python backend\\main.py";
    }
    if (status === 400) {
      return detail || "That message can't be sent. Check it isn't empty " +
        "or longer than " + MAX_CHARS + " characters.";
    }
    if (status === 429) {
      return "Too many questions in a short time. Wait a minute, then try again.";
    }
    return "The assistant couldn't answer just now. Try again in a moment.";
  }

  function send(question) {
    var text = question.trim();
    if (!text || busy) return;
    if (text.length > MAX_CHARS) {
      addMessage("error", describeError(400));
      return;
    }

    var suggestions = log.querySelector(".chat-suggestions");
    if (suggestions) suggestions.remove();

    addMessage("user", text);
    input.value = "";
    setBusy(true);

    var thinking = addMessage("bot", "Looking that up…");
    thinking.classList.add("chat-msg-pending");

    fetch(API_URL + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    })
      .then(function (response) {
        return response.json().catch(function () { return {}; })
          .then(function (body) { return { status: response.status, body: body }; });
      })
      .then(function (result) {
        thinking.remove();
        if (result.status === 200 && result.body.answer) {
          var bubble = addMessage("bot", result.body.answer);
          renderSources(bubble, result.body.sources, result.body.answer);
          var mentioned = result.body.answer.match(/BRE-[SR]-\d+/);
          if (mentioned) lastPropertyRef = mentioned[0];
        } else {
          var detail = typeof result.body.detail === "string" ? result.body.detail : "";
          addMessage("error", describeError(result.status, detail));
        }
      })
      .catch(function () {
        // fetch rejects with no status when the server is down, or when the
        // browser blocks the response because of CORS.
        thinking.remove();
        addMessage("error", describeError(0));
      })
      .then(function () {
        setBusy(false);
        input.focus();
        log.scrollTop = log.scrollHeight;
      });
  }

  // -------------------------------------------------------------------------
  // Opening, closing and keyboard handling
  // -------------------------------------------------------------------------

  function openPanel() {
    panel.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    launcher.hidden = true;
    if (launcherRobot) launcherRobot.pause();
    input.focus();
  }

  function closePanel() {
    panel.hidden = true;
    launcher.hidden = false;
    launcher.setAttribute("aria-expanded", "false");
    animate(launcherRobot);
    launcher.focus();
  }

  // -------------------------------------------------------------------------
  // Talking to a person (Task 2.3: FR-07, FR-08, FR-09, FR-13)
  //
  // Two steps, deliberately. First the visitor is asked whether they want to
  // share their details. Only if they say yes does the form appear (FR-08).
  // -------------------------------------------------------------------------

  var leadOpen = false;

  function field(form, id, labelText, attrs, hint) {
    var wrap = el("div", { class: "lead-field" });
    wrap.appendChild(el("label", { for: id }, labelText));
    var input = el(attrs.tag || "input", Object.assign({ id: id, name: id }, attrs.attrs));
    wrap.appendChild(input);
    if (hint) wrap.appendChild(el("p", { class: "lead-hint", id: id + "-hint" }, hint));
    if (hint) input.setAttribute("aria-describedby", id + "-hint");
    form.appendChild(wrap);
    return input;
  }

  // FastAPI's 422 lists problems as {loc: ["body", "phone"], msg: "Value error, ..."}.
  // Turn them into the sentences written in backend/leads.py.
  function leadProblems(detail) {
    var names = { name: "Enter your name.", phone: "Enter your phone number.",
                  consent: "Details can only be sent once you have agreed to share them." };
    if (!Array.isArray(detail)) return [typeof detail === "string" ? detail : "Check the details and try again."];
    return detail.map(function (problem) {
      var key = problem.loc && problem.loc[problem.loc.length - 1];
      var msg = String(problem.msg || "").replace(/^Value error,\s*/, "");
      if (problem.type === "missing" && names[key]) return names[key];
      return msg || "Check the details and try again.";
    });
  }

  function offerHandoff() {
    if (leadOpen) return;
    leadOpen = true;
    handoffButton.disabled = true;

    var suggestions = log.querySelector(".chat-suggestions");
    if (suggestions) suggestions.remove();

    addMessage("bot",
      "I can pass your details to the Bella Real Estate team so someone can " +
      "call you back. Would you like to share your name and phone number?");

    var choice = el("div", { class: "chat-suggestions" });
    var yes = el("button", { type: "button", class: "chat-chip" }, "Yes, share my details");
    var no = el("button", { type: "button", class: "chat-chip" }, "Not now");
    choice.appendChild(yes);
    choice.appendChild(no);
    log.appendChild(choice);
    log.scrollTop = log.scrollHeight;
    yes.focus();

    yes.addEventListener("click", function () {
      choice.remove();
      addMessage("user", "Yes, share my details");
      showLeadForm();
    });
    no.addEventListener("click", function () {
      choice.remove();
      addMessage("user", "Not now");
      addMessage("bot", "No problem. Ask me anything else about our properties.");
      closeLead();
    });
  }

  function closeLead() {
    leadOpen = false;
    handoffButton.disabled = false;
    input.focus();
  }

  function showLeadForm() {
    var card = el("form", { class: "lead-form", novalidate: "" });
    card.appendChild(el("h3", { class: "lead-title" }, "Your contact details"));
    var problems = el("div", { class: "lead-problems", role: "alert" });
    card.appendChild(problems);

    var name = field(card, "lead-name", "Name", { attrs: {
      type: "text", autocomplete: "name", maxlength: "80", required: "" } });
    var phone = field(card, "lead-phone", "Phone", { attrs: {
      type: "tel", autocomplete: "tel", inputmode: "tel", maxlength: "24", required: "" } },
      "For example 0300 1234567");
    var email = field(card, "lead-email", "Email (optional)", { attrs: {
      type: "email", autocomplete: "email", maxlength: "254" } });
    var ref = field(card, "lead-ref", "Property reference (optional)", { attrs: {
      type: "text", maxlength: "9", value: lastPropertyRef, placeholder: "BRE-R-202" } });
    var note = field(card, "lead-note", "Note (optional)", { tag: "textarea", attrs: {
      rows: "2", maxlength: "500" } });

    // Hidden from people, including screen-reader users. Bots fill it in.
    var trap = el("input", { type: "text", name: "website", tabindex: "-1",
      autocomplete: "off", class: "lead-trap", "aria-hidden": "true" });
    card.appendChild(trap);

    card.appendChild(el("p", { class: "lead-privacy" },
      "Your details go to the owner of this demo site and are used only to " +
      "reply to this enquiry. Bella Real Estate is a fictional company."));

    var buttons = el("div", { class: "lead-buttons" });
    var submit = el("button", { type: "submit", class: "chat-send" }, "Send my details");
    var cancel = el("button", { type: "button", class: "chat-chip" }, "Cancel");
    buttons.appendChild(submit);
    buttons.appendChild(cancel);
    card.appendChild(buttons);

    log.appendChild(card);
    log.scrollTop = log.scrollHeight;
    name.focus();

    function showProblems(list) {
      problems.textContent = "";
      if (!list.length) return;
      var ul = el("ul");
      list.forEach(function (text) { ul.appendChild(el("li", null, text)); });
      problems.appendChild(ul);
      log.scrollTop = card.offsetTop;
    }

    cancel.addEventListener("click", function () {
      card.remove();
      addMessage("bot", "Cancelled. Nothing was sent.");
      closeLead();
    });

    card.addEventListener("submit", function (event) {
      event.preventDefault();

      // Quick checks so the visitor doesn't wait for the server to say the
      // obvious. The server checks again; its rules are the ones that count.
      var local = [];
      if (!name.value.trim()) local.push("Enter your name.");
      if (!/^\+?\d{10,15}$/.test(phone.value.replace(/[\s\-().]/g, "")))
        local.push("Enter a phone number with 10 to 15 digits, for example 0300 1234567.");
      if (local.length) { showProblems(local); return; }
      showProblems([]);

      submit.disabled = true;
      submit.textContent = "Sending…";

      fetch(API_URL + "/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.value, phone: phone.value, email: email.value,
          property_ref: ref.value, message: note.value,
          consent: true,   // set only on this path, after "Yes, share my details"
          website: trap.value
        })
      })
        .then(function (response) {
          return response.json().catch(function () { return {}; })
            .then(function (body) { return { status: response.status, body: body }; });
        })
        .then(function (result) {
          if (result.status === 200 && result.body.status === "received") {
            card.remove();
            var first = name.value.trim().split(/\s+/)[0];
            addMessage("bot",
              "Thank you, " + first + ". Your details have been received " +
              "(reference " + result.body.lead_id + ").\n\n" +
              "Because Bella Real Estate is fictional, no agent will call. " +
              "Your details went to the owner of this demo site.");
            closeLead();
            return;
          }
          if (result.status === 422) {
            showProblems(leadProblems(result.body.detail));
          } else {
            showProblems([describeError(result.status)]);
          }
          submit.disabled = false;
          submit.textContent = "Send my details";
        })
        .catch(function () {
          showProblems([describeError(0)]);
          submit.disabled = false;
          submit.textContent = "Send my details";
        });
    });
  }

  handoffButton.addEventListener("click", offerHandoff);

  launcher.addEventListener("click", openPanel);
  closeButton.addEventListener("click", closePanel);

  panel.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closePanel();
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    send(input.value);
  });

  // Enter sends; Shift+Enter starts a new line.
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send(input.value);
    }
  });
})();
