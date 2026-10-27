"use strict";

// Similar Artists page. Plain script: no framework, nothing loaded from other sites.
// Every value from the server reaches the page as text (textContent or setAttribute), never as
// markup. The rules are BR3.1 to BR3.3 and BR4.1 to BR4.13 of the u3-web design.
(function () {
  const SUGGEST_DELAY_MS = 150;
  const PAGE_SIZE = 20;
  const MAX_GENRES = 3;
  const LINK_PREFIXES = {
    musicbrainz: "https://musicbrainz.org/artist/",
    youtube: "https://www.youtube.com/results?search_query=",
    spotify: "https://open.spotify.com/search/",
  };
  const LINK_LABELS = {
    musicbrainz: " on MusicBrainz",
    youtube: " on YouTube",
    spotify: " on Spotify",
  };

  const searchInput = document.getElementById("artist-search");
  const clearButton = document.getElementById("clear-search");
  const suggestionList = document.getElementById("suggestions");
  const liveStatus = document.getElementById("live-status");
  const resultsPanel = document.getElementById("results-panel");
  const resultsHeading = document.getElementById("results-heading");
  const resultsMessage = document.getElementById("results-message");
  const placeholderRows = document.getElementById("placeholder-rows");
  const resultsList = document.getElementById("results-list");
  const retryButton = document.getElementById("retry-button");
  const showMoreButton = document.getElementById("show-more");
  const iconTemplate = document.getElementById("link-icons");

  // Suggestion state: only the newest request's reply is ever shown.
  let suggestRequest = 0;
  let suggestTimer = null;
  let suggestions = [];
  let highlighted = -1;

  // Results state: resultsRequest drops replies that arrive after a newer pick or Back.
  let resultsRequest = 0;
  let busy = false;
  let currentId = "";
  let shown = 0;
  let retryAction = null;

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function announce(message) {
    liveStatus.textContent = "";
    liveStatus.textContent = message;
  }

  // ---- Suggestions -------------------------------------------------------------------------

  function closeSuggestions() {
    suggestions = [];
    highlighted = -1;
    suggestionList.replaceChildren();
    suggestionList.hidden = true;
    searchInput.setAttribute("aria-expanded", "false");
    searchInput.removeAttribute("aria-activedescendant");
  }

  function setHighlight(index) {
    const options = suggestionList.querySelectorAll("[role='option']");
    options.forEach(function (option, position) {
      option.setAttribute("aria-selected", position === index ? "true" : "false");
    });
    highlighted = index;
    if (index >= 0 && options[index]) {
      searchInput.setAttribute("aria-activedescendant", options[index].id);
      options[index].scrollIntoView({ block: "nearest" });
    } else {
      searchInput.removeAttribute("aria-activedescendant");
    }
  }

  function suggestionRow(artist, position) {
    const row = make("li", "suggestion");
    row.id = "suggestion-" + position;
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", "false");
    row.appendChild(make("div", "suggestion-name", artist.name));
    const parts = [];
    if (artist.description) {
      parts.push(artist.description);
    }
    if (artist.genres && artist.genres.length > 0) {
      parts.push(artist.genres[0]);
    }
    if (parts.length > 0) {
      row.appendChild(make("div", "suggestion-detail", parts.join(" · ")));
    }
    // Keep focus in the search box while the pointer picks a row.
    row.addEventListener("mousedown", function (event) {
      event.preventDefault();
    });
    row.addEventListener("click", function () {
      pick(artist);
    });
    return row;
  }

  function showSuggestions(list, text) {
    suggestions = list;
    highlighted = -1;
    suggestionList.replaceChildren();
    if (list.length === 0) {
      const empty = make("li", "suggestion-empty", "No artists match '" + text + "'");
      empty.setAttribute("role", "presentation");
      suggestionList.appendChild(empty);
      announce("No artists match '" + text + "'");
    } else {
      list.forEach(function (artist, position) {
        suggestionList.appendChild(suggestionRow(artist, position));
      });
      announce(list.length + (list.length === 1 ? " suggestion available" : " suggestions available"));
    }
    suggestionList.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
    searchInput.removeAttribute("aria-activedescendant");
  }

  async function fetchSuggestions(text) {
    suggestRequest += 1;
    const number = suggestRequest;
    try {
      const response = await fetch("/api/suggest?q=" + encodeURIComponent(text));
      if (!response.ok) {
        throw new Error("suggestions unavailable");
      }
      const list = await response.json();
      if (number === suggestRequest) {
        showSuggestions(list, text);
      }
    } catch (error) {
      // A failed suggestion request closes the list quietly; the user can keep typing.
      if (number === suggestRequest) {
        closeSuggestions();
      }
    }
  }

  function updateClearButton() {
    clearButton.hidden = searchInput.value.length === 0;
  }

  function onInput() {
    clearTimeout(suggestTimer);
    updateClearButton();
    const text = searchInput.value;
    if (text.trim() === "") {
      suggestRequest += 1; // a reply still in flight must not reopen the list
      closeSuggestions();
      return;
    }
    suggestTimer = setTimeout(function () {
      fetchSuggestions(text);
    }, SUGGEST_DELAY_MS);
  }

  function onKeyDown(event) {
    const open = !suggestionList.hidden && suggestions.length > 0;
    switch (event.key) {
      case "ArrowDown":
        if (open) {
          event.preventDefault();
          setHighlight(highlighted + 1 >= suggestions.length ? 0 : highlighted + 1);
        }
        break;
      case "ArrowUp":
        if (open) {
          event.preventDefault();
          setHighlight(highlighted <= 0 ? suggestions.length - 1 : highlighted - 1);
        }
        break;
      case "Enter":
        if (open && highlighted >= 0) {
          event.preventDefault();
          pick(suggestions[highlighted]);
        }
        break;
      case "Escape":
        if (!suggestionList.hidden) {
          event.preventDefault();
          closeSuggestions();
        }
        break;
      case "Tab":
        closeSuggestions();
        break;
      default:
        break;
    }
  }

  function clearSearch() {
    clearTimeout(suggestTimer);
    suggestRequest += 1;
    searchInput.value = "";
    closeSuggestions();
    updateClearButton();
    searchInput.focus(); // the results and the address stay as they are
  }

  // ---- Results -----------------------------------------------------------------------------

  function setMessage(text) {
    resultsMessage.textContent = text;
  }

  function showPlaceholders() {
    placeholderRows.replaceChildren();
    for (let n = 0; n < 5; n += 1) {
      placeholderRows.appendChild(make("li", "placeholder-row"));
    }
    placeholderRows.hidden = false;
  }

  function hidePlaceholders() {
    placeholderRows.replaceChildren();
    placeholderRows.hidden = true;
  }

  function linkIcon(kind) {
    const source = iconTemplate.content.querySelector("[data-icon='" + kind + "']");
    return source ? source.cloneNode(true) : null;
  }

  function linkElement(kind, url, name) {
    if (typeof url !== "string" || !url.startsWith(LINK_PREFIXES[kind])) {
      return null; // only the three expected web addresses are ever used
    }
    const link = make("a", "icon-link");
    link.setAttribute("href", url);
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
    link.setAttribute("aria-label", name + LINK_LABELS[kind]);
    link.setAttribute("title", name + LINK_LABELS[kind]);
    const icon = linkIcon(kind);
    if (icon) {
      link.appendChild(icon);
    }
    return link;
  }

  function resultRow(item, rank) {
    const artist = item.artist;
    const row = make("li", "result-row");
    row.appendChild(make("span", "rank", String(rank)));

    const name = make("button", "artist-name", artist.name);
    name.setAttribute("type", "button");
    name.addEventListener("click", function () {
      navigate(artist.mbid, true);
    });
    row.appendChild(name);

    const similarity = "similarity " + Number(item.cosine).toFixed(2);
    const track = make("div", "bar-track");
    track.setAttribute("title", similarity);
    const fill = make("div", "bar-fill");
    fill.setAttribute("aria-hidden", "true");
    fill.style.width = Math.max(0, Math.min(1, Number(item.bar))) * 100 + "%";
    track.appendChild(fill);
    track.appendChild(make("span", "sr-only", similarity));
    row.appendChild(track);

    const genres = make("div", "genres");
    if (artist.genres && artist.genres.length > 0) {
      artist.genres.slice(0, MAX_GENRES).forEach(function (genre) {
        genres.appendChild(make("span", "genre-tag", genre));
      });
    } else {
      genres.appendChild(make("span", "no-genres", "no genres listed"));
    }
    row.appendChild(genres);

    const links = make("div", "links");
    Object.keys(LINK_PREFIXES).forEach(function (kind) {
      const link = linkElement(kind, item.links ? item.links[kind] : null, artist.name);
      if (link) {
        links.appendChild(link);
      }
    });
    row.appendChild(links);
    return row;
  }

  function setActions(hasMore, failed) {
    retryButton.hidden = !failed;
    showMoreButton.hidden = !hasMore || failed;
    showMoreButton.disabled = busy;
  }

  function showFailure(action) {
    retryAction = action;
    setMessage("Something went wrong finding similar artists. Try again.");
    setActions(false, true);
  }

  // Fetches one page. Returns { status, body } or null when the network fails.
  async function fetchSimilar(id, offset) {
    try {
      const address =
        "/api/artists/" +
        encodeURIComponent(id) +
        "/similar?offset=" +
        offset +
        "&limit=" +
        PAGE_SIZE;
      const response = await fetch(address);
      const body = response.ok ? await response.json() : null;
      return { status: response.status, body: body };
    } catch (error) {
      return null;
    }
  }

  async function loadArtist(id, focusHeading) {
    resultsRequest += 1;
    const number = resultsRequest;
    currentId = id;
    shown = 0;
    busy = true;
    retryAction = function () {
      loadArtist(id, focusHeading);
    };
    resultsPanel.hidden = false;
    resultsList.replaceChildren();
    resultsHeading.textContent = "Finding similar artists";
    setMessage("");
    setActions(false, false);
    showPlaceholders();

    const reply = await fetchSimilar(id, 0);
    if (number !== resultsRequest) {
      return; // a newer pick or Back replaced this one
    }
    busy = false;
    hidePlaceholders();
    if (reply === null || (!reply.body && reply.status !== 404 && reply.status !== 422)) {
      resultsHeading.textContent = "Similar artists";
      showFailure(retryAction);
      return;
    }
    if (reply.status === 404 || reply.status === 422) {
      resultsHeading.textContent = "Similar artists";
      setMessage("We don't know this artist.");
      setActions(false, false);
      announce("We don't know this artist.");
      return;
    }
    const data = reply.body;
    searchInput.value = data.artist.name;
    updateClearButton();
    resultsHeading.textContent = "Artists like " + data.artist.name;
    if (data.items.length === 0) {
      const message = "Not enough listening data to find artists like " + data.artist.name + ".";
      setMessage(message);
      setActions(false, false);
      announce(message);
    } else {
      appendRows(data.items);
      setMessage("");
      setActions(data.has_more, false);
    }
    if (focusHeading) {
      resultsHeading.focus();
    }
  }

  function appendRows(items) {
    const fragment = document.createDocumentFragment();
    items.forEach(function (item, position) {
      fragment.appendChild(resultRow(item, shown + position + 1));
    });
    const first = fragment.firstElementChild;
    resultsList.appendChild(fragment);
    shown += items.length;
    return first;
  }

  async function showMore() {
    if (busy || !currentId) {
      return; // one request at a time: a double click never adds a page twice
    }
    busy = true;
    showMoreButton.disabled = true;
    const number = resultsRequest;
    const id = currentId;
    retryAction = showMore;
    const reply = await fetchSimilar(id, shown);
    if (number !== resultsRequest) {
      return;
    }
    busy = false;
    if (reply === null || !reply.body) {
      showFailure(showMore);
      return;
    }
    const first = appendRows(reply.body.items);
    setMessage("");
    setActions(reply.body.has_more, false);
    announce(reply.body.items.length + " more artists");
    if (first) {
      const target = first.querySelector(".artist-name");
      if (target) {
        target.focus();
      }
    }
  }

  function retry() {
    if (busy || !retryAction) {
      return;
    }
    setMessage("");
    retryButton.hidden = true;
    retryAction();
  }

  // ---- Addresses and history ---------------------------------------------------------------

  function idFromAddress() {
    const match = window.location.pathname.match(/^\/artist\/([^/]+)\/?$/);
    if (!match) {
      return "";
    }
    try {
      return decodeURIComponent(match[1]);
    } catch (error) {
      return match[1];
    }
  }

  function navigate(id, push) {
    if (push) {
      window.history.pushState({ id: id }, "", "/artist/" + encodeURIComponent(id));
    }
    closeSuggestions();
    loadArtist(id, push);
  }

  function pick(artist) {
    clearTimeout(suggestTimer);
    suggestRequest += 1; // a suggestion reply still in flight must not reopen the list
    searchInput.value = artist.name;
    updateClearButton();
    navigate(artist.mbid, true);
  }

  function showAddress() {
    const id = idFromAddress();
    if (id) {
      loadArtist(id, false);
    } else {
      resultsRequest += 1; // drop any reply still in flight
      busy = false;
      resultsPanel.hidden = true;
    }
  }

  searchInput.addEventListener("input", onInput);
  searchInput.addEventListener("keydown", onKeyDown);
  clearButton.addEventListener("click", clearSearch);
  showMoreButton.addEventListener("click", showMore);
  retryButton.addEventListener("click", retry);
  window.addEventListener("popstate", showAddress);
  document.addEventListener("click", function (event) {
    if (!event.target.closest(".search-wrap")) {
      closeSuggestions();
    }
  });

  searchInput.focus();
  updateClearButton();
  showAddress();
})();
