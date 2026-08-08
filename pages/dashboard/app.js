const bridge = window.AstrBotPluginPage;
let messageTimer;

const state = {
  games: [],
  game: null,
  subscriptionId: null,
  timerId: null,
  elapsed: 0,
  home: true,
  selectedSessionId: "",
  resultKey: null,
  mode: "open",
};

const elements = {
  toolbar: document.getElementById("toolbar"),
  home: document.getElementById("home"),
  session: document.getElementById("session"),
  sessionSummary: document.getElementById("session-summary"),
  sessionMenu: document.getElementById("session-menu"),
  restartSession: document.getElementById("restart-session"),
  pushBoard: document.getElementById("push-board"),
  difficulty: document.getElementById("difficulty"),
  emptyState: document.getElementById("empty-state"),
  start: document.getElementById("start"),
  mineCount: document.getElementById("mine-count"),
  openedCount: document.getElementById("opened-count"),
  elapsed: document.getElementById("elapsed"),
  board: document.getElementById("board"),
  boardFrame: document.getElementById("board-frame"),
  openMode: document.getElementById("open-mode"),
  markMode: document.getElementById("mark-mode"),
  sweepMode: document.getElementById("sweep-mode"),
  message: document.getElementById("message"),
  help: document.getElementById("help"),
  helpPc: document.getElementById("help-pc"),
  helpMobile: document.getElementById("help-mobile"),
  resultModal: document.getElementById("game-result"),
  resultTitle: document.getElementById("result-title"),
  resultSummary: document.getElementById("result-summary"),
  resultStats: document.getElementById("result-stats"),
  resultClose: document.getElementById("result-close"),
  resultNew: document.getElementById("result-new"),
};

function t(key, fallback) {
  return bridge.t(`pages.dashboard.${key}`, fallback);
}

function formatElapsed(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function renderText() {
  document.title = t("title", "Minesweeper");
  elements.home.textContent = "\u2302";
  elements.home.setAttribute("aria-label", t("home", "Home"));
  elements.home.title = t("home", "Home");
  elements.restartSession.textContent = t("restartSession", "Restart");
  elements.session.setAttribute("aria-label", t("session", "Session"));
  elements.sessionSummary.setAttribute("aria-label", t("session", "Session"));
  elements.pushBoard.setAttribute("aria-label", t("pushBoard", "Push board"));
  elements.pushBoard.title = t("pushBoard", "Push board");
  elements.difficulty.setAttribute("aria-label", t("difficulty", "Difficulty"));
  elements.start.textContent = t("start", "Start");
  elements.openMode.textContent = t("open", "Open");
  elements.markMode.textContent = t("mark", "Mark");
  elements.sweepMode.textContent = t("sweep", "Sweep");
  elements.helpPc.textContent = t("helpPc", "Left click to open, right click to mark, middle click or click an open cell to sweep.");
  elements.helpMobile.textContent = t("helpMobile", "Use the buttons below to open, mark, or sweep.");
  elements.resultClose.textContent = t("close", "Close");
  elements.resultNew.textContent = t("newGame", "New game");
  renderGame();
  renderSessions();
}

function showMessage(message, error = false) {
  clearTimeout(messageTimer);
  elements.message.textContent = message || "";
  elements.message.classList.toggle("error", error);
  elements.message.classList.toggle("show", Boolean(message));
  if (message) {
    messageTimer = setTimeout(() => {
      elements.message.classList.remove("show");
    }, error ? 4000 : 2500);
  }
}

function setMode(mode) {
  state.mode = mode;
  [elements.openMode, elements.markMode, elements.sweepMode].forEach((button) => {
    button.classList.toggle("active", button === elements[`${mode}Mode`]);
  });
}

function updateBoardSize() {
  const game = state.game;
  if (!game) return;

  const frameStyle = getComputedStyle(elements.boardFrame);
  const boardStyle = getComputedStyle(elements.board);
  const width =
    elements.boardFrame.clientWidth -
    parseFloat(frameStyle.paddingLeft) -
    parseFloat(frameStyle.paddingRight);
  const height =
    elements.boardFrame.clientHeight -
    parseFloat(frameStyle.paddingTop) -
    parseFloat(frameStyle.paddingBottom);
  const gap = parseFloat(boardStyle.columnGap);
  const tileSize = Math.floor(
    Math.min(
      (width - gap * (game.cols - 1)) / game.cols,
      (height - gap * (game.rows - 1)) / game.rows,
    ),
  );
  elements.board.style.setProperty("--tile-size", `${Math.max(tileSize, 1)}px`);
}

function updateTimer() {
  elements.elapsed.textContent = `${t("elapsed", "Time")} ${formatElapsed(state.elapsed)}`;
}

function syncTimer() {
  const active = state.game && !["win", "fail"].includes(state.game.state);
  if (!active) {
    clearInterval(state.timerId);
    state.timerId = null;
    return;
  }
  if (!state.timerId) {
    state.timerId = setInterval(() => {
      state.elapsed += 1;
      updateTimer();
    }, 1000);
  }
}

function showResult(game) {
  const key = `${game.session_id}:${game.state}`;
  if (state.resultKey === key) return;
  state.resultKey = key;
  const won = game.state === "win";
  elements.resultTitle.textContent = won ? t("winTitle", "You win") : t("failTitle", "Game over");
  elements.resultSummary.textContent = won ? t("winSummary", "Well done!") : t("failSummary", "Better luck next time.");
  elements.resultStats.textContent = `${t("elapsed", "Time")} ${formatElapsed(game.elapsed)} / ${t("opened", "Opened")} ${game.opened}`;
  elements.resultModal.hidden = false;
}

function closeResult() {
  elements.resultModal.hidden = true;
}

function renderGame() {
  const game = state.game;
  const active = game && !["win", "fail"].includes(game.state);
  elements.start.textContent = active ? t("stop", "Stop") : t("start", "Start");
  elements.mineCount.textContent = game
    ? `${t("mines", "Mines")} ${game.mines - game.marked}`
    : "";
  elements.openedCount.textContent = game
    ? `${t("opened", "Opened")} ${game.opened}`
    : "";
  if (game) {
    state.elapsed = game.elapsed;
    updateTimer();
    if (!active) showResult(game);
  } else {
    state.elapsed = 0;
    updateTimer();
  }
  elements.toolbar.hidden = !game && (state.home || !state.games.length);
  elements.toolbar.classList.toggle("game-active", Boolean(game));
  elements.restartSession.hidden = !["win", "fail"].includes(game?.state);
  elements.pushBoard.hidden = !game?.can_push;
  elements.emptyState.classList.toggle("hidden", Boolean(game));
  elements.boardFrame.classList.toggle("hidden", !game);
  [elements.openMode, elements.markMode, elements.sweepMode].forEach((button) => {
    button.disabled = !active;
  });
  elements.board.replaceChildren();
  syncTimer();
  if (!game) return;

  elements.board.style.setProperty("--cols", game.cols);
  elements.board.style.setProperty("--rows", game.rows);
  updateBoardSize();
  game.tiles.forEach((row, rowIndex) => {
    row.forEach((tile, colIndex) => {
      const button = document.createElement("button");
      button.className = "tile";
      button.type = "button";
       button.disabled = !active;
       button.dataset.state = tile.open ? "open" : "closed";
       if (tile.open && tile.count) button.classList.add(`number-${tile.count}`);
       if (tile.marked) button.textContent = "\u2691";
      else if (tile.mine) button.textContent = "\u2739";
      else if (tile.open && tile.count) button.textContent = tile.count;
      button.classList.toggle("boom", tile.boom);
      button.addEventListener("click", () => performAction(rowIndex, colIndex, tile.open ? "sweep" : "open"));
      button.addEventListener("mousedown", (event) => {
        if (event.button === 1) {
          event.preventDefault();
          performAction(rowIndex, colIndex, "sweep");
        }
      });
      button.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        performAction(rowIndex, colIndex, "mark");
      });
      elements.board.append(button);
    });
  });
}

function renderSessions() {
  const selected = state.game?.session_id || state.selectedSessionId;
  elements.sessionMenu.replaceChildren();
  const selectedGame = state.games.find((game) => game.session_id === selected);
  elements.sessionSummary.textContent = selectedGame?.display_name || selected || "";

  state.games.forEach((game) => {
    const row = document.createElement("div");
    row.className = "session-item";
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", String(game.session_id === selected));

    const selectButton = document.createElement("button");
    selectButton.type = "button";
    selectButton.className = "session-item-main";
    selectButton.textContent = game.display_name || game.session_id;
    selectButton.addEventListener("click", () => {
      elements.session.open = false;
      selectGame(game.session_id);
    });

    row.append(selectButton);

    const stopButton = document.createElement("button");
    stopButton.type = "button";
    stopButton.className = "session-item-stop";
    stopButton.textContent = "\u00d7";
    stopButton.setAttribute("aria-label", t("stopSession", "Stop game"));
    stopButton.title = t("stopSession", "Stop game");
    stopButton.addEventListener("click", (event) => {
      event.stopPropagation();
      stopSession(game.session_id);
    });

    row.append(stopButton);
    elements.sessionMenu.append(row);
  });
}

function renderDifficulties(difficulties) {
  const selected = elements.difficulty.value;
  elements.difficulty.replaceChildren();
  difficulties.forEach((difficulty) => {
    const option = document.createElement("option");
    option.value = difficulty;
    option.textContent = difficulty;
    elements.difficulty.append(option);
  });
  if (difficulties.includes(selected)) elements.difficulty.value = selected;
}

async function refreshGames() {
  try {
    const result = await bridge.apiGet("games");
    state.games = result.games || [];
    renderDifficulties(result.difficulties || []);
    renderSessions();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function pushBoard() {
  if (!state.game?.can_push) return;
  try {
    elements.pushBoard.disabled = true;
    await bridge.apiPost("push", { session_id: state.game.session_id });
    showMessage(t("pushSuccess", "Board pushed"));
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    elements.pushBoard.disabled = false;
  }
}

async function selectGame(sessionId) {
  await closeSubscription();
  state.selectedSessionId = sessionId;
  if (!sessionId) {
    state.game = null;
    renderGame();
    return;
  }
  try {
    closeResult();
    state.home = false;
    state.game = await bridge.apiGet("game", { session_id: sessionId });
    renderGame();
    renderSessions();
    state.subscriptionId = await bridge.subscribeSSE(
      "events",
      {
        onMessage(event) {
          if (event.parsed?.session_id === sessionId) {
            state.game = event.parsed;
            renderGame();
            if (event.parsed.type === "stopped") {
              state.game = null;
              closeSubscription();
              refreshGames();
            }
          }
        },
        onError() {
          showMessage(t("disconnected", "Disconnected"), true);
        },
      },
      { session_id: sessionId },
    );
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function performAction(row, col, action = state.mode) {
  if (!state.game || state.game.state === "win" || state.game.state === "fail") return;
  if (state.game.tiles[row]?.[col]?.open && action !== "sweep") return;
  try {
    state.game = await bridge.apiPost("action", {
      session_id: state.game.session_id,
      action,
      row,
      col,
    });
    renderGame();
    refreshGames();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function startGame() {
  if (state.game?.state === "prepare" || state.game?.state === "gaming") {
    await stopGame();
    return;
  }
  try {
    closeResult();
    state.home = false;
    const sessionId = state.game?.session_id;
    const displayName = `${t("gameName", "Minesweeper game")}${state.games.length + 1}`;
    const payload = {
      difficulty: elements.difficulty.value,
      display_name: displayName,
    };
    if (sessionId) payload.session_id = sessionId;
    const game = await bridge.apiPost("games", payload);
    await refreshGames();
    await selectGame(game.session_id);
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function goHome() {
  await closeSubscription();
  closeResult();
  state.game = null;
  state.home = true;
  renderGame();
}

async function stopGame() {
  if (!state.game) return;
  try {
    await bridge.apiPost("stop", { session_id: state.game.session_id });
    await closeSubscription();
    state.game = null;
    renderGame();
    await refreshGames();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function closeSubscription() {
  if (state.subscriptionId) {
    await bridge.unsubscribeSSE(state.subscriptionId);
    state.subscriptionId = null;
  }
}

async function initialize() {
  await bridge.ready();
  renderText();
  setMode("open");
  new ResizeObserver(updateBoardSize).observe(elements.boardFrame);
  await refreshGames();
}

async function stopSession(sessionId) {
  try {
    await bridge.apiPost("stop", { session_id: sessionId });
    if (state.game?.session_id === sessionId) {
      await closeSubscription();
      state.game = null;
      state.selectedSessionId = "";
      renderGame();
    }
    await refreshGames();
  } catch (error) {
    showMessage(error.message, true);
  }
}

elements.home.addEventListener("click", goHome);
elements.session.addEventListener("toggle", () => {
  if (elements.session.open) refreshGames();
});
elements.restartSession.addEventListener("click", startGame);
elements.pushBoard.addEventListener("click", pushBoard);
elements.start.addEventListener("click", startGame);
elements.openMode.addEventListener("click", () => setMode("open"));
elements.markMode.addEventListener("click", () => setMode("mark"));
elements.sweepMode.addEventListener("click", () => setMode("sweep"));
elements.resultClose.addEventListener("click", closeResult);
elements.resultNew.addEventListener("click", () => {
  closeResult();
  startGame();
});
window.addEventListener("beforeunload", () => {
  closeSubscription();
});
bridge.onContext(renderText);
initialize();
