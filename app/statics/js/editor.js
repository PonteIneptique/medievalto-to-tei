"use strict";
(function() {
  const inp = document.querySelector("#xml"),
        preview = document.querySelector("#preview"),
        //CETEIcean = new CETEI({ignoreFragmentId: true}),
        results = document.querySelector("#results"),
        results_ul = results.querySelector("ul"),
        form = document.querySelector("#form-tei");

  const gather_regex = /\[([^\|\]]+|[^\|\]]*\[\s+\][^\|\]]*)\|([^\]]+)\]/gm,
        spaces = /\s/;

  const formatText = (before, after, previous) => {
    let start, end, len, text;
    if (previous === true) {
      start = inp.selectionStart-1;
      end = inp.selectionEnd;
    } else {
      start = inp.selectionStart;
      end = inp.selectionEnd;
    }
    len = inp.value.length;
    text = inp.value.substring(start, end);

    if (after !== undefined && after !== false && text) {
      inp.value = inp.value.substring(0, start) + before + text + after.replace("$$1", text) + inp.value.substring(end, len);
      let selection = start + before.length + after.replace("$$1", text).length + text.length;
      inp.setSelectionRange(selection, selection);
    }
    else {
      inp.value = inp.value.substring(0, start) + before + inp.value.substring(end, len);
      inp.setSelectionRange(start + before.length, start + before.length);
    }
  }

  const updateTEI = function(){
    preview.innerHTML = inp.value.replace(gather_regex, "<choice><abbr>$1</abbr><expan>$2</expan></choice>")
                        .replace(/(\[[^\|\]]\]+)/gm, "<choice type=\"hyphenization\"><orig>$1</orig><corr></corr></choice>")
                        .replace(/•/gm, "<choice type=\"add-space\"><orig></orig><corr> </corr></choice>")
                        .replace(/\r?\n/g, "<lb></lb>");
  }


  document.querySelectorAll("#toolbar a").forEach(function (element) {
    if (element.getAttribute("data-before", null) == null) {
      if (element.id === "save-doc") {
       element.addEventListener("click", async function(event) {
         event.preventDefault();
         submit();
       });
      } else {
       element.addEventListener("click", function(event) {
        let logs = {},
            gather_abbr = Object.fromEntries(
              [...inp.value.matchAll(gather_regex)].map(match => [match[1], match[2]])
            ),
            text = inp.value;

        Object.entries(gather_abbr).forEach(([abbr, expan]) => {
          var reg = new RegExp(`(([\\.\\s]+)(?<!\\[)${abbr}(?!\\|)([\\.\\s]))`, "gm"),
              repl = `$2[${abbr}|${expan}]$3`;
          logs[abbr] = [...text.matchAll(reg)].length;
          console.log([...text.matchAll(reg)]);
          text = text.replace(reg, repl);
        });

        inp.value = text;
        results_ul.innerHTML = "";
        results_ul.innerHTML = Object.entries(logs).map(([key, val]) => `<li><em>${key}</em>: ${val} found</li>`).join("\n");
        results.style.display = "block";
      });
      }
    } else {
      let before = element.getAttribute("data-before"),
          after = element.getAttribute("data-after", null);
      element.addEventListener("click", function(event) {
        event.preventDefault();
        formatText(before, after);
        updateTEI();
      });
    }
  });

  document.querySelector("#toggle-hide").addEventListener("click", function() {
    preview.classList.toggle("hide-orig");
  });

  results.querySelector(".btn-close").addEventListener("click", function(e) {
    e.preventDefault();
    console.log("HI");
    results.style.display = "none";
  });

  inp.addEventListener("keydown", async function(e) {
    if (e.key === "[" && inp.selectionStart !== inp.selectionEnd) {
      e.preventDefault();
      formatText("[","|]");
    } else if (e.key === "Backspace" && e.shiftKey === true && inp.value.substring(inp.selectionStart-1, inp.selectionEnd).match(spaces) !== null) {
      e.preventDefault();
      formatText("[", "]", true);
    } else if (e.key === " " && e.shiftKey === true) {
      e.preventDefault();
      formatText("•", false, false);
    } else if (e.key === "Enter" && e.ctrlKey === true) {
      e.preventDefault();
      updateTEI();
    } else if (e.key === "s" && e.ctrlKey === true) {
      e.preventDefault();
      updateTEI();
      await submit();
    }
  });

  inp.addEventListener("change", updateTEI);
  updateTEI();

  const submit = async function() {
    let response = await fetch(form.getAttribute("action"), {
      method: 'POST',
      body: new FormData(form)
    });
    let result = await response.json();
  };

  form.addEventListener("submit", async function (event){
    event.preventDefault();
    alert("Submit ?");
    await submit();
    alert(result.message);
  });
})();