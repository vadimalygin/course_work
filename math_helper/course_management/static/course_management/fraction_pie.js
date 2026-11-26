const pieNamespace = "http://www.w3.org/2000/svg";
const pieColors = ["#5b9bd5", "#e98b59", "#68ad83", "#aa83c7", "#e0b548"];

const pieConfigurations = {
  "ratio.png": {
    mode: "partition",
    title: "Разделите круг на равные части",
    numerator: 0,
    denominator: 1,
  },
  "cake.jpg": {
    mode: "partition",
    title: "Попробуйте разделить пирог на равные части",
    numerator: 0,
    denominator: 8,
  },
  "ratio 1-8.png": {
    mode: "partition",
    title: "Измените число равных частей круга",
    numerator: 0,
    denominator: 8,
  },
  "ratio 1-8 2.png": {
    mode: "fraction",
    title: "Выберите одну из восьми равных частей",
    numerator: 1,
    denominator: 8,
  },
  "ratio 3-8.png": {
    mode: "fraction",
    title: "Отметьте три восьмых круга",
    numerator: 3,
    denominator: 8,
  },
  "ratio 3+2 8.png": {
    mode: "addition",
    title: "Сложите дроби с одинаковыми знаменателями",
    first: 3,
    second: 2,
    denominator: 8,
  },
  "ratio 3х2 8.png": {
    mode: "multiplication",
    title: "Умножение дроби как повторное сложение",
    numerator: 2,
    denominator: 8,
    repetitions: 3,
  },
  "ratio 12 + 13.png": {
    mode: "different-addition",
    title: "Сложите дроби с разными знаменателями",
    firstNumerator: 1,
    firstDenominator: 2,
    secondNumerator: 1,
    secondDenominator: 3,
  },
  "ratio 1-3 2 1-2 3.png": {
    mode: "equivalent",
    title: "Разбейте половины и трети на одинаковые части",
    firstNumerator: 1,
    firstDenominator: 2,
    secondNumerator: 1,
    secondDenominator: 3,
    targetDenominator: 6,
  },
  "ratio 36 26.png": {
    mode: "addition",
    title: "Сложите три шестых и две шестых",
    first: 3,
    second: 2,
    denominator: 6,
  },
  "ratio 36 2.png": {
    mode: "division",
    title: "Разделите три шестых на две равные группы",
    numerator: 3,
    denominator: 6,
    divisor: 2,
  },
};

function createPieElement(tagName, attributes = {}) {
  const element = document.createElementNS(pieNamespace, tagName);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  return element;
}

function addPieInput(controls, labelText, name, value, maximum = 12) {
  const label = document.createElement("label");
  label.className = "d-grid gap-1 small";
  label.append(document.createTextNode(labelText));
  const input = document.createElement("input");
  input.className = "form-control form-control-sm";
  input.type = "number";
  input.name = name;
  input.min = name.toLowerCase().includes("denominator") || name === "divisor" ? "1" : "0";
  input.max = String(maximum);
  input.step = "1";
  input.value = String(value);
  input.defaultValue = String(value);
  input.inputMode = "numeric";
  label.append(input);
  controls.append(label);
  return input;
}

function addPieButton(controls, text, callback) {
  const button = document.createElement("button");
  button.className = "btn btn-sm btn-outline theme-primary";
  button.type = "button";
  button.textContent = text;
  button.addEventListener("click", callback);
  controls.append(button);
}

function makePieChart(label, numerator, denominator, colorForSlice) {
  const card = document.createElement("div");
  card.className = "card p-2 text-center";
  card.setAttribute("aria-label", label);
  const caption = document.createElement("span");
  caption.className = "small fw-semibold";
  caption.textContent = label;
  card.append(caption);

  const chartRow = document.createElement("div");
  chartRow.className = "d-flex justify-content-center flex-wrap gap-1";
  const wholeCount = Math.max(1, Math.ceil(numerator / denominator));
  for (let whole = 0; whole < wholeCount; whole += 1) {
    const svg = createPieElement("svg", {
      width: "160",
      height: "160",
      class: "img-fluid",
      viewBox: "0 0 160 160",
      role: "img",
      "aria-label": `${numerator} из ${denominator}`,
    });
    const center = 80;
    const radius = 66;

    if (denominator === 1) {
      svg.append(createPieElement("circle", {
        cx: center, cy: center, r: radius,
        fill: colorForSlice(whole * denominator),
        stroke: "#d18b45", "stroke-width": "1.5",
      }));
    } else {
      for (let part = 0; part < denominator; part += 1) {
        const start = -Math.PI / 2 + (part * Math.PI * 2) / denominator;
        const end = -Math.PI / 2 + ((part + 1) * Math.PI * 2) / denominator;
        const startX = center + radius * Math.cos(start);
        const startY = center + radius * Math.sin(start);
        const endX = center + radius * Math.cos(end);
        const endY = center + radius * Math.sin(end);
        const largeArc = end - start > Math.PI ? 1 : 0;
        const globalPart = whole * denominator + part;
        svg.append(createPieElement("path", {
          d: `M ${center} ${center} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY} Z`,
          fill: colorForSlice(globalPart),
          stroke: "#d18b45",
          "stroke-width": "1.5",
        }));
      }
    }

    svg.append(createPieElement("circle", {
      cx: center, cy: center, r: radius,
      fill: "none", stroke: "#2878d0", "stroke-width": "1.5",
    }));
    chartRow.append(svg);
  }
  card.append(chartRow);
  return card;
}

function fractionColor(numerator, color = pieColors[0]) {
  return (part) => part < numerator ? color : "#fff";
}

function validFraction(numerator, denominator) {
  return Number.isInteger(numerator) && Number.isInteger(denominator)
    && numerator >= 0 && numerator <= denominator
    && denominator >= 1 && denominator <= 12;
}

function greatestCommonDivisor(first, second) {
  let a = first;
  let b = second;
  while (b) [a, b] = [b, a % b];
  return a;
}

function leastCommonMultiple(first, second) {
  return (first / greatestCommonDivisor(first, second)) * second;
}

function makePieWidget(image, config) {
  const widget = document.createElement("section");
  widget.className = "card border-subtle-primary bg-1 rounded-2 p-3";
  const widgetColumn = document.createElement("div");
  widgetColumn.className = "col-12 md:col-8";
  const widgetRow = document.createElement("div");
  widgetRow.className = "row g-0 justify-content-center mb-4";
  widgetColumn.append(widget);
  widgetRow.append(widgetColumn);
  widget.setAttribute("aria-label", "Интерактивная модель дроби");
  widget.dataset.pieMode = config.mode;
  widget.dataset.pieImage = image.getAttribute("name") || "";
  widget.innerHTML = `
    <h2 class="h6 fw-semibold mb-3"></h2>
    <div class="d-flex justify-content-center flex-wrap gap-2 my-2" aria-live="polite"></div>
    <div class="d-flex align-items-end flex-wrap gap-2 mt-3"></div>
    <p class="small mt-2 mb-0" role="status"></p>
  `;
  const [heading, charts, controls, status] = widget.children;
  heading.textContent = config.title;

  const input = (label, name, value, max = 12) => (
    addPieInput(controls, label, name, value, max)
  );
  const addChart = (label, numerator, denominator, colors = fractionColor(numerator)) => {
    charts.append(makePieChart(label, numerator, denominator, colors));
  };
  const clearCharts = () => charts.replaceChildren();
  const reset = () => {
    widget.querySelectorAll("input").forEach((field) => {
      field.value = field.defaultValue;
    });
    update();
  };
  const addReset = () => addPieButton(controls, "Сбросить", reset);
  let update = () => {};

  if (config.mode === "partition" || config.mode === "fraction") {
    const numerator = input("Числитель", "numerator", config.numerator, 12);
    const denominator = input("Знаменатель", "denominator", config.denominator, 12);
    update = () => {
      const top = numerator.valueAsNumber;
      const bottom = denominator.valueAsNumber;
      clearCharts();
      if (!validFraction(top, bottom)) {
        status.textContent = "Выберите числитель от 0 до знаменателя и знаменатель от 1 до 12.";
        return;
      }
      addChart("Выбранная часть", top, bottom);
      status.textContent = `Закрашено ${top} из ${bottom} равных частей: ${top}/${bottom}.`;
    };
    [numerator, denominator].forEach((field) => field.addEventListener("input", update));
  } else if (config.mode === "addition") {
    const first = input("Первое слагаемое", "first", config.first, 12);
    const second = input("Второе слагаемое", "second", config.second, 12);
    const denominator = input("Общий знаменатель", "denominator", config.denominator, 12);
    update = () => {
      const a = first.valueAsNumber;
      const b = second.valueAsNumber;
      const bottom = denominator.valueAsNumber;
      clearCharts();
      if (!validFraction(a, bottom) || !validFraction(b, bottom)) {
        status.textContent = "Числители должны быть от 0 до общего знаменателя.";
        return;
      }
      addChart("Первое слагаемое", a, bottom);
      addChart("Второе слагаемое", b, bottom, fractionColor(b, pieColors[1]));
      addChart("Сумма", a + b, bottom, (part) => (
        part < a ? pieColors[0] : (part < a + b ? pieColors[1] : "#fff")
      ));
      status.textContent = `${a}/${bottom} + ${b}/${bottom} = ${a + b}/${bottom}.`;
    };
    [first, second, denominator].forEach((field) => field.addEventListener("input", update));
  } else if (config.mode === "multiplication") {
    const numerator = input("Числитель дроби", "numerator", config.numerator, 12);
    const denominator = input("Знаменатель", "denominator", config.denominator, 12);
    const repetitions = input("Количество повторений", "repetitions", config.repetitions, 6);
    const perform = () => update();
    addPieButton(controls, "Показать умножение", perform);
    update = () => {
      const top = numerator.valueAsNumber;
      const bottom = denominator.valueAsNumber;
      const count = repetitions.valueAsNumber;
      clearCharts();
      if (!validFraction(top, bottom) || !Number.isInteger(count) || count < 0 || count > 6) {
        status.textContent = "Введите дробь от 0 до 1 и число повторений от 0 до 6.";
        return;
      }
      for (let repeat = 0; repeat < count; repeat += 1) {
        addChart(`Слагаемое ${repeat + 1}`, top, bottom);
      }
      const total = top * count;
      addChart("Произведение", total, bottom, (part) => (
        part < total ? pieColors[Math.floor(part / Math.max(top, 1)) % pieColors.length] : "#fff"
      ));
      const repeatedSum = Array.from({ length: count }, () => `${top}/${bottom}`).join(" + ") || "0";
      status.textContent = `${count} × ${top}/${bottom} = ${repeatedSum} = ${total}/${bottom}.`;
    };
    [numerator, denominator, repetitions].forEach((field) => field.addEventListener("input", update));
  } else if (config.mode === "different-addition") {
    const firstNumerator = input("Числитель первой дроби", "firstNumerator", config.firstNumerator);
    const firstDenominator = input("Знаменатель первой дроби", "firstDenominator", config.firstDenominator);
    const secondNumerator = input("Числитель второй дроби", "secondNumerator", config.secondNumerator);
    const secondDenominator = input("Знаменатель второй дроби", "secondDenominator", config.secondDenominator);
    update = () => {
      const a = firstNumerator.valueAsNumber;
      const d1 = firstDenominator.valueAsNumber;
      const b = secondNumerator.valueAsNumber;
      const d2 = secondDenominator.valueAsNumber;
      clearCharts();
      if (!validFraction(a, d1) || !validFraction(b, d2)) {
        status.textContent = "Введите две правильные дроби со знаменателями от 1 до 12.";
        return;
      }
      const common = leastCommonMultiple(d1, d2);
      if (common > 24) {
        status.textContent = "Общий знаменатель больше 24; выберите меньшие знаменатели.";
        return;
      }
      const equivalentFirst = a * (common / d1);
      const equivalentSecond = b * (common / d2);
      const total = equivalentFirst + equivalentSecond;
      addChart("Первая дробь", a, d1);
      addChart("Вторая дробь", b, d2, fractionColor(b, pieColors[1]));
      addChart("Сумма в общих долях", total, common, (part) => (
        part < equivalentFirst ? pieColors[0]
          : (part < total ? pieColors[1] : "#fff")
      ));
      status.textContent = `${a}/${d1} = ${equivalentFirst}/${common}; ${b}/${d2} = ${equivalentSecond}/${common}; сумма ${total}/${common}.`;
    };
    [firstNumerator, firstDenominator, secondNumerator, secondDenominator]
      .forEach((field) => field.addEventListener("input", update));
  } else if (config.mode === "equivalent") {
    const firstNumerator = input("Числитель первой дроби", "firstNumerator", config.firstNumerator);
    const firstDenominator = input("Знаменатель первой дроби", "firstDenominator", config.firstDenominator);
    const secondNumerator = input("Числитель второй дроби", "secondNumerator", config.secondNumerator);
    const secondDenominator = input("Знаменатель второй дроби", "secondDenominator", config.secondDenominator);
    const target = input("Общий знаменатель", "targetDenominator", config.targetDenominator, 24);
    const expand = () => {
      const d1 = firstDenominator.valueAsNumber;
      const d2 = secondDenominator.valueAsNumber;
      if (Number.isInteger(d1) && Number.isInteger(d2) && d1 > 0 && d2 > 0) {
        target.value = String(leastCommonMultiple(d1, d2));
      }
      update();
    };
    addPieButton(controls, "Найти общий знаменатель", expand);
    update = () => {
      const a = firstNumerator.valueAsNumber;
      const d1 = firstDenominator.valueAsNumber;
      const b = secondNumerator.valueAsNumber;
      const d2 = secondDenominator.valueAsNumber;
      const common = target.valueAsNumber;
      clearCharts();
      if (!validFraction(a, d1) || !validFraction(b, d2)
        || !Number.isInteger(common) || common < 1 || common > 24
        || common % d1 !== 0 || common % d2 !== 0) {
        status.textContent = "Общий знаменатель должен делиться на оба исходных знаменателя.";
        return;
      }
      const expandedFirst = a * (common / d1);
      const expandedSecond = b * (common / d2);
      addChart(`${a}/${d1}`, a, d1);
      addChart(`${expandedFirst}/${common}`, expandedFirst, common);
      addChart(`${b}/${d2}`, b, d2, fractionColor(b, pieColors[1]));
      addChart(`${expandedSecond}/${common}`, expandedSecond, common, fractionColor(expandedSecond, pieColors[1]));
      status.textContent = `${a}/${d1} = ${expandedFirst}/${common}; ${b}/${d2} = ${expandedSecond}/${common}.`;
    };
    [firstNumerator, firstDenominator, secondNumerator, secondDenominator, target]
      .forEach((field) => field.addEventListener("input", update));
  } else if (config.mode === "division") {
    const numerator = input("Числитель", "numerator", config.numerator);
    const denominator = input("Знаменатель", "denominator", config.denominator);
    const divisor = input("Делитель", "divisor", config.divisor);
    update = () => {
      const top = numerator.valueAsNumber;
      const bottom = denominator.valueAsNumber;
      const by = divisor.valueAsNumber;
      clearCharts();
      if (!validFraction(top, bottom) || !Number.isInteger(by) || by < 1 || by > 12
        || bottom * by > 24) {
        status.textContent = "Введите дробь от 0 до 1 и делитель, чтобы новый знаменатель не превышал 24.";
        return;
      }
      addChart("Исходная дробь", top, bottom);
      addChart("После деления", top, bottom * by);
      status.textContent = `${top}/${bottom} ÷ ${by} = ${top}/${bottom * by}.`;
    };
    [numerator, denominator, divisor].forEach((field) => field.addEventListener("input", update));
  }

  addReset();

  update();
  (image.closest("p") || image).insertAdjacentElement("afterend", widgetRow);
}

const courseContent = document.querySelector(".course-step-content");
if (courseContent?.dataset.courseLesson === "9") {
  courseContent.querySelectorAll("img[name]").forEach((image) => {
    const imageName = (image.getAttribute("name") || "").toLowerCase();
    const config = pieConfigurations[imageName];
    if (config) makePieWidget(image, config);
  });
}
