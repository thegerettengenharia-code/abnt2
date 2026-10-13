(function () {
  "use strict";

  var MAX_BYTES = 50 * 1024 * 1024;
  var DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

  var themeToggle = document.getElementById("theme-toggle");
  var fileWarning = document.getElementById("file-warning");
  var form = document.getElementById("form");
  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("file-input");
  var fileName = document.getElementById("file-name");
  var fontSelect = document.getElementById("font");
  var submitBtn = document.getElementById("submit");
  var progress = document.getElementById("progress");
  var progressBar = document.getElementById("progress-bar");
  var errorBox = document.getElementById("error");
  var result = document.getElementById("result");
  var downloadLink = document.getElementById("download");
  var foundList = document.getElementById("found");
  var changesList = document.getElementById("changes");
  var pendingList = document.getElementById("pending");

  var selectedFile = null;

  if (window.location.protocol === "file:") {
    fileWarning.hidden = false;
  }

  /* ---------- Tema ---------- */
  themeToggle.addEventListener("click", function () {
    var current = document.documentElement.getAttribute("data-theme");
    var next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("abnt-theme", next); } catch (e) {}
  });

  /* ---------- Seleção de arquivo ---------- */
  function setError(message) {
    if (!message) {
      errorBox.hidden = true;
      errorBox.textContent = "";
      return;
    }
    errorBox.hidden = false;
    errorBox.textContent = message;
  }

  function validateFile(file) {
    if (!file) return "Escolha um arquivo.";
    var name = (file.name || "").toLowerCase();
    if (!name.endsWith(".docx") && !name.endsWith(".pdf")) {
      return "Formato não aceito. Envie um arquivo .docx ou .pdf.";
    }
    if (file.size > MAX_BYTES) {
      return "O arquivo tem " + (file.size / 1048576).toFixed(1) + " MB. O limite é 50 MB.";
    }
    return null;
  }

  function applyFile(file) {
    var problem = validateFile(file);
    if (problem) {
      setError(problem);
      selectedFile = null;
      fileName.hidden = true;
      dropzone.classList.remove("is-set");
      return;
    }
    setError(null);
    selectedFile = file;
    fileName.textContent = file.name + "  ·  " + (file.size / 1048576).toFixed(2) + " MB";
    fileName.hidden = false;
    dropzone.classList.add("is-set");
  }

  fileInput.addEventListener("change", function () {
    if (fileInput.files && fileInput.files[0]) applyFile(fileInput.files[0]);
  });

  dropzone.addEventListener("click", function () { fileInput.click(); });
  dropzone.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      fileInput.click();
    }
  });

  ["dragenter", "dragover"].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      dropzone.classList.add("is-drag");
    });
  });
  ["dragleave", "drop"].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      if (type === "dragleave" && dropzone.contains(event.relatedTarget)) return;
      dropzone.classList.remove("is-drag");
    });
  });
  dropzone.addEventListener("drop", function (event) {
    var files = event.dataTransfer && event.dataTransfer.files;
    if (files && files[0]) applyFile(files[0]);
  });

  /* ---------- Envio ---------- */
  function setProgress(pct) {
    progress.hidden = false;
    progressBar.style.width = Math.max(0, Math.min(100, pct)) + "%";
  }

  function resetButton() {
    submitBtn.disabled = false;
    submitBtn.textContent = "Formatar documento";
  }

  function parseDetail(text, fallback) {
    try {
      var payload = JSON.parse(text);
      if (payload && payload.detail) return payload.detail;
    } catch (e) {}
    return fallback;
  }

  function presign(file) {
    return fetch("/api/presign", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ filename: file.name, size: file.size })
    }).then(function (response) {
      if (!response.ok) {
        return response.text().then(function (text) {
          throw new Error(parseDetail(text, "Não foi possível preparar o envio."));
        });
      }
      return response.json();
    });
  }

  function uploadToBlob(info, file) {
    return new Promise(function (resolve, reject) {
      var storeId = info.store_id || "";
      var requestId = storeId + ":" + Date.now() + ":" + Math.random().toString(16).slice(2);
      var xhr = new XMLHttpRequest();
      xhr.open("PUT", info.upload_url);
      xhr.setRequestHeader("x-api-version", "12");
      xhr.setRequestHeader("x-vercel-blob-store-id", storeId);
      xhr.setRequestHeader("x-api-blob-request-id", requestId);
      xhr.setRequestHeader("x-api-blob-request-attempt", "0");
      xhr.setRequestHeader("x-vercel-blob-access", "public");
      xhr.setRequestHeader("x-content-type", file.type || "application/octet-stream");

      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 55) + 5);
        }
      };
      xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
          var payload = null;
          try { payload = JSON.parse(xhr.responseText); } catch (e) {}
          resolve(payload || {});
        } else {
          var detail = parseDetail(xhr.responseText, "Falha ao enviar o arquivo.");
          if (xhr.status === 413) detail = "O arquivo excede o limite permitido (50 MB).";
          reject(new Error(detail));
        }
      };
      xhr.onerror = function () {
        reject(new Error("Falha de conexão ao enviar o arquivo. Tente novamente."));
      };
      xhr.send(file);
    });
  }

  function requestFormat(info, file) {
    return fetch("/api/format", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        pathname: info.pathname,
        filename: file.name,
        font: fontSelect.value
      })
    }).then(function (response) {
      if (!response.ok) {
        return response.text().then(function (text) {
          throw new Error(parseDetail(text, "Não foi possível formatar o arquivo."));
        });
      }
      return response.json();
    });
  }

  function cleanup(pathname) {
    if (!pathname) return;
    try {
      fetch("/api/cleanup", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ pathname: pathname })
      }).catch(function () {});
    } catch (e) {}
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!selectedFile) {
      setError("Escolha um arquivo .docx ou .pdf antes de continuar.");
      dropzone.focus();
      return;
    }

    setError(null);
    result.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Enviando...";
    setProgress(6);

    var file = selectedFile;
    var info = null;

    presign(file)
      .then(function (presigned) {
        info = presigned;
        submitBtn.textContent = "Enviando arquivo...";
        return uploadToBlob(presigned, file);
      })
      .then(function () {
        setProgress(65);
        submitBtn.textContent = "Formatando...";
        return requestFormat(info, file);
      })
      .then(function (payload) {
        setProgress(92);
        return loadResult(payload);
      })
      .then(function () {
        setProgress(100);
        setTimeout(function () {
          progress.hidden = true;
          progressBar.style.width = "0";
        }, 400);
        resetButton();
      })
      .catch(function (error) {
        progress.hidden = true;
        progressBar.style.width = "0";
        resetButton();
        setError(error && error.message
          ? error.message
          : "Não foi possível processar o arquivo. Tente novamente.");
      });
  });

  function loadResult(payload) {
    var url = payload.result_url;
    if (!url) {
      return Promise.reject(new Error("O servidor não devolveu o arquivo corrigido."));
    }
    return fetch(url)
      .then(function (response) {
        if (!response.ok) throw new Error("Não foi possível baixar o arquivo corrigido.");
        return response.blob();
      })
      .then(function (blob) {
        renderResult(payload, blob);
        cleanup(payload.result_pathname);
      })
      .catch(function () {
        // Se o download via fetch falhar, ainda oferecemos o link direto.
        renderResult(payload, null);
        cleanup(payload.result_pathname);
      });
  }

  /* ---------- Relatório ---------- */
  function renderResult(payload, blob) {
    var report = payload.report || {};
    var labelMap = {
      corpo_paragrafos: "Parágrafos do corpo (recuo 1,25 cm, 1,5)",
      citacoes_longas: "Citações longas (recuo 4 cm, tam. 10, simples, sem aspas)",
      legendas: "Legendas (tam. 10)",
      fontes: "Fontes de ilustrações/tabelas (tam. 10)",
      referencias: "Referências (simples, à esquerda, linha em branco entre cada)",
      notas_rodape: "Notas de rodapé (tam. 10, simples, separador 5 cm)",
      tabelas_sem_bordas_verticais: "Tabelas sem bordas laterais/verticais"
    };

    foundList.innerHTML = "";
    (report.encontrados || []).forEach(function (item) {
      var li = document.createElement("li");
      li.textContent = item;
      foundList.appendChild(li);
    });
    (report.faltando || []).forEach(function (item) {
      var li = document.createElement("li");
      li.className = "is-missing";
      li.textContent = item + " (não encontrado)";
      foundList.appendChild(li);
    });
    if (!foundList.children.length) {
      var empty = document.createElement("li");
      empty.textContent = "Nenhum elemento padrão identificado.";
      foundList.appendChild(empty);
    }

    changesList.innerHTML = "";
    var alteracoes = report.alteracoes || {};
    Object.keys(labelMap).forEach(function (key) {
      var value = alteracoes[key];
      if (value === undefined) return;
      var li = document.createElement("li");
      var span = document.createElement("span");
      span.textContent = labelMap[key];
      var b = document.createElement("b");
      b.textContent = value;
      li.appendChild(span);
      li.appendChild(b);
      changesList.appendChild(li);
    });

    pendingList.innerHTML = "";
    (report.pendencias || []).forEach(function (item) {
      var li = document.createElement("li");
      li.textContent = item;
      pendingList.appendChild(li);
    });

    if (blob) {
      downloadLink.href = URL.createObjectURL(blob);
    } else {
      downloadLink.href = payload.result_url;
    }
    downloadLink.setAttribute("download", payload.filename || "documento_ABNT.docx");
    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }
})();
