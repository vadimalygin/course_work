const svgNamespace = "http://www.w3.org/2000/svg";

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(svgNamespace, tagName);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  return element;
}

function getNumberLineConfig(imageName, lessonNumber, stepNumber) {
  const name = imageName.toLowerCase().replace(/\.png$/i, "");
  const config = {
    minimum: -11,
    maximum: 11,
    initialPoint: 0,
    distance: 1,
    reverseAxis: false,
    mode: "arithmetic",
    multiplicand: 3,
    repetitions: 2,
    divisor: 2,
    fractionalQuotient: false,
  };

  if (lessonNumber === 4 && stepNumber === 6) {
    const naturalLine = { minimum: 1, maximum: 11 };
    if (name === "natural number line") {
      Object.assign(config, naturalLine, { initialPoint: 1 });
    } else if (name === "natural number line +1") {
      Object.assign(config, naturalLine, { initialPoint: 1, distance: 1 });
    } else if (name === "natural number line +3") {
      Object.assign(config, naturalLine, { initialPoint: 4, distance: 3 });
    } else if (name === "natural number line +1+1+1") {
      Object.assign(config, naturalLine, { initialPoint: 4, distance: 1 });
    } else if (name === "natural number line -1") {
      Object.assign(config, naturalLine, { initialPoint: 2, distance: 1 });
    }
  }

  if (lessonNumber === 5 && stepNumber === 1) {
    if (name === "natural number line over the edge") {
      Object.assign(config, { minimum: 0, maximum: 11, initialPoint: 1, distance: 1 });
    } else if (name === "natural number line over the edge thrice") {
      Object.assign(config, { minimum: -2, maximum: 11, initialPoint: 1, distance: 1 });
    }
  }

  if (lessonNumber === 5 && stepNumber === 3 && name === "natural number line 0") {
    Object.assign(config, { minimum: 0, maximum: 11, initialPoint: 1, distance: 1 });
  }

  if (lessonNumber === 7 && stepNumber === 8) {
    if (name === "natural number line") {
      Object.assign(config, { minimum: 1, maximum: 11, initialPoint: 1 });
    } else if (name === "natural number line start 0") {
      Object.assign(config, { minimum: 0, maximum: 11, initialPoint: 0 });
    } else if (name === "natural number line reversed") {
      Object.assign(config, {
        minimum: 0,
        maximum: 11,
        initialPoint: 0,
        reverseAxis: true,
      });
    } else if (name === "whole number line direction") {
      Object.assign(config, { minimum: 0, maximum: 11, initialPoint: 0 });
    }
  }

  if (lessonNumber === 7 && stepNumber >= 9) {
    Object.assign(config, {
      minimum: stepNumber === 14 ? -23 : -11,
      maximum: stepNumber === 14 ? 23 : 11,
      initialPoint: 0,
      mode: "multiplication",
    });

    if (name === "whole number line +1") {
      Object.assign(config, { multiplicand: 1, repetitions: 1 });
    } else if (name === "whole number line +3") {
      Object.assign(config, { multiplicand: 3, repetitions: 1 });
    } else if (name === "whole number line 3х2") {
      Object.assign(config, { multiplicand: 3, repetitions: 2 });
    } else if (name === "whole number line 3х" || name === "whole number line 3 = 1") {
      Object.assign(config, { multiplicand: 3, repetitions: 1 });
    } else if (name === "whole number line streched -4-1") {
      Object.assign(config, { multiplicand: -4, repetitions: -1 });
    } else if (name === "whole number line streched -4") {
      Object.assign(config, { multiplicand: -4, repetitions: 1 });
    } else if (name === "whole number line streched -4х-5") {
      Object.assign(config, { multiplicand: -4, repetitions: -5 });
    }
  }

  if (lessonNumber === 8 && stepNumber === 1
    && name.startsWith("whole number line streched 2")) {
    Object.assign(config, {
      minimum: -11,
      maximum: 11,
      initialPoint: name.endsWith("2 11") ? 11 : 10,
      mode: "division",
      divisor: 2,
    });
  }

  if (lessonNumber === 9 && stepNumber === 5 && name === "whole number line 3х") {
    Object.assign(config, {
      minimum: -11,
      maximum: 11,
      initialPoint: 2,
      mode: "division",
      divisor: 3,
      fractionalQuotient: true,
    });
  }

  return config;
}

function addNumberLine(image) {
  const imageName = image.getAttribute("name") || "";
  const courseContent = document.querySelector(".course-step-content");
  const lessonNumber = Number(courseContent?.dataset.courseLesson);
  const stepNumber = Number(courseContent?.dataset.courseStep);
  const isGenericWholeLine = lessonNumber === 7 && stepNumber === 8
    && imageName.toLowerCase() === "line.png";
  if (!/^(natural|whole) number line\b/i.test(imageName) && !isGenericWholeLine) return;

  const config = getNumberLineConfig(imageName, lessonNumber, stepNumber);
  const {
    minimum,
    maximum,
    initialPoint,
    distance,
    mode,
    reverseAxis,
    multiplicand,
    repetitions,
    divisor,
    fractionalQuotient,
  } = config;
  const multiplicationMode = mode === "multiplication";
  const divisionMode = mode === "division";
  const span = maximum - minimum;
  const width = Math.max(680, span * 30 + 56);
  const left = 28;
  const right = width - 28;

  const widget = document.createElement("section");
  widget.className = "card border-subtle-primary bg-1 rounded-2 p-3";
  if (span > 22) widget.classList.add("overflow-auto");
  const widgetColumn = document.createElement("div");
  widgetColumn.className = "col-12 md:col-8";
  const widgetRow = document.createElement("div");
  widgetRow.className = "row g-0 justify-content-center mb-4";
  widgetColumn.append(widget);
  widgetRow.append(widgetColumn);
  widget.setAttribute("aria-label", "Интерактивная числовая прямая");
  if (multiplicationMode) widget.dataset.multiplication = "";
  if (divisionMode) widget.dataset.division = "";
  widget.innerHTML = `
    <h2 class="h6 fw-semibold mb-3">${
      multiplicationMode ? "Умножение на числовой прямой"
        : divisionMode ? "Деление на числовой прямой"
          : "Попробуйте на числовой прямой"
    }</h2>
    <div class="overflow-auto"><svg role="img" aria-label="Числовая прямая от ${minimum} до ${maximum}"></svg></div>
    ${multiplicationMode ? `
      <div class="d-flex align-items-end flex-wrap gap-2 mt-3">
        <label class="d-grid gap-1 small">Слагаемое
          <input class="form-control form-control-sm" data-multiplicand type="number" min="-10" max="10" step="1" value="${multiplicand}" inputmode="numeric">
        </label>
        <label class="d-grid gap-1 small">Количество повторений
          <input class="form-control form-control-sm" data-repetitions type="number" min="-10" max="10" step="1" value="${repetitions}" inputmode="numeric">
        </label>
        <button class="btn btn-sm btn-outline theme-primary" type="button" data-multiply>Показать умножение</button>
        <button class="btn btn-sm btn-subtle theme-secondary" type="button" data-reset>Сбросить</button>
      </div>
      <p class="small opacity-75 mt-2 mb-0">Умножение показано как последовательное сложение одинакового слагаемого.</p>
    ` : divisionMode ? `
      <div class="d-flex align-items-end flex-wrap gap-2 mt-3">
        <label class="d-grid gap-1 small">Делимое
          <input class="form-control form-control-sm" data-dividend type="number" min="${minimum}" max="${maximum}" step="1" value="${initialPoint}" inputmode="numeric">
        </label>
        <label class="d-grid gap-1 small">Делитель
          <input class="form-control form-control-sm" data-divisor type="number" min="1" max="${span}" step="1" value="${divisor}" inputmode="numeric">
        </label>
        <button class="btn btn-sm btn-outline theme-primary" type="button" data-divide>Показать деление</button>
        <button class="btn btn-sm btn-subtle theme-secondary" type="button" data-reset>Сбросить</button>
      </div>
      <p class="small opacity-75 mt-2 mb-0">${
        fractionalQuotient
          ? "Положение результата показывает дробное частное на числовой прямой."
          : "Деление показано как повторное вычитание делителя."
      }</p>
    ` : `
      <div class="d-flex align-items-end flex-wrap gap-2 mt-3">
        <label class="d-grid gap-1 small">Начальная точка
          <input class="form-range" data-point type="range" min="${minimum}" max="${maximum}" step="1" value="${initialPoint}">
        </label>
        <label class="d-grid gap-1 small">Шаги
          <input class="form-control form-control-sm" data-distance type="number" min="${-span}" max="${span}" step="1" value="${distance}" inputmode="numeric">
        </label>
        <button class="btn btn-sm btn-outline theme-primary" type="button" data-operation="add">Прибавить</button>
        <button class="btn btn-sm btn-outline theme-primary" type="button" data-operation="subtract">Вычесть</button>
        <button class="btn btn-sm btn-subtle theme-secondary" type="button" data-reset>Сбросить</button>
      </div>
    `}
    <p class="small mt-2 mb-0" data-status aria-live="polite"></p>
  `;

  const svg = widget.querySelector("svg");
  const pointInput = widget.querySelector("[data-point]");
  const distanceInput = widget.querySelector("[data-distance]");
  const dividendInput = widget.querySelector("[data-dividend]");
  const divisorInput = widget.querySelector("[data-divisor]");
  const status = widget.querySelector("[data-status]");
  let point = initialPoint;
  let jumps = [];

  const xFor = (value) => {
    const position = reverseAxis ? maximum - value : value - minimum;
    return left + (position / span) * (right - left);
  };
  const selectPoint = (value) => {
    point = Math.max(minimum, Math.min(maximum, value));
    if (pointInput) pointInput.value = String(point);
    jumps = [];
    status.textContent = `Выбрана точка: ${point}.`;
    render();
  };

  function render() {
    const axisY = 72 + Math.max(0, jumps.length - 1) * 20;
    svg.setAttribute("viewBox", `0 0 ${width} ${axisY + 48}`);
    svg.replaceChildren();
    svg.append(createSvgElement("line", {
      x1: left, y1: axisY, x2: right, y2: axisY,
      stroke: "#1677ff", "stroke-width": "2",
    }));

    for (let value = minimum; value <= maximum; value += 1) {
      const x = xFor(value);
      svg.append(createSvgElement("line", {
        x1: x, y1: axisY - 8, x2: x, y2: axisY + 8,
        stroke: "#1677ff", "stroke-width": "1.5",
      }));
      const label = createSvgElement("text", {
        x, y: axisY + 28, "text-anchor": "middle",
        fill: "#3d454c", "font-size": "14",
      });
      label.textContent = String(value);
      svg.append(label);
    }

    jumps.forEach((jump, index) => {
      const startX = xFor(jump.start);
      const endX = xFor(jump.end);
      const middleX = (startX + endX) / 2;
      const arcY = axisY - 28 - index * 18;
      svg.append(createSvgElement("path", {
        d: `M ${startX} ${axisY - 3} Q ${middleX} ${arcY} ${endX} ${axisY - 3}`,
        fill: "none", stroke: "#f18a30", "stroke-width": "2.5",
      }));
      const direction = Math.sign(endX - startX);
      if (direction) {
        svg.append(createSvgElement("path", {
          d: `M ${endX} ${axisY - 3} l ${-direction * 7} -5 l ${direction * 1} 8 z`,
          fill: "#f18a30",
        }));
      }
    });

    svg.append(createSvgElement("circle", {
      cx: xFor(point), cy: axisY, r: "7",
      fill: "#e8cd63", stroke: "#fff", "stroke-width": "2",
    }));
  }

  if (pointInput) {
    pointInput.addEventListener("input", () => selectPoint(Number(pointInput.value)));

    svg.addEventListener("click", (event) => {
      const bounds = svg.getBoundingClientRect();
      if (!bounds.width) return;
      const svgX = ((event.clientX - bounds.left) / bounds.width) * width;
      const position = ((svgX - left) / (right - left)) * span;
      const value = Math.round(reverseAxis ? maximum - position : minimum + position);
      selectPoint(value);
    });
  }

  widget.querySelectorAll("[data-operation]").forEach((button) => {
    button.addEventListener("click", () => {
      const distance = distanceInput.valueAsNumber;
      if (!Number.isInteger(distance)) {
        status.textContent = "Введите целое число шагов.";
        return;
      }

      const direction = button.dataset.operation === "add" ? 1 : -1;
      const result = point + direction * distance;
      if (result < minimum || result > maximum) {
        status.textContent = `Результат ${result} за пределами этой прямой (${minimum}…${maximum}).`;
        return;
      }

      const start = point;
      jumps.push({ start, end: result });
      point = result;
      pointInput.value = String(point);
      const operator = direction > 0 ? "+" : "−";
      const signedDistance = distance < 0 ? `(${distance})` : distance;
      status.textContent = `${start} ${operator} ${signedDistance} = ${result}`;
      render();
    });
  });

  const divideButton = widget.querySelector("[data-divide]");
  if (divideButton) {
    divideButton.addEventListener("click", () => {
      const dividend = dividendInput.valueAsNumber;
      const currentDivisor = divisorInput.valueAsNumber;
      if (!Number.isInteger(dividend) || dividend < minimum || dividend > maximum
        || !Number.isInteger(currentDivisor) || currentDivisor <= 0) {
        status.textContent = "Введите целое делимое и положительный целый делитель.";
        return;
      }

      jumps = [];
      if (fractionalQuotient) {
        const quotient = dividend / currentDivisor;
        const wholeSteps = Math.floor(Math.abs(quotient));
        const direction = Math.sign(quotient);
        point = 0;
        for (let index = 0; index < wholeSteps; index += 1) {
          const nextPoint = point + direction;
          jumps.push({ start: point, end: nextPoint });
          point = nextPoint;
        }
        if (Math.abs(quotient - point) > Number.EPSILON) {
          jumps.push({ start: point, end: quotient });
        }
        point = quotient;
        const displayedQuotient = Number(quotient.toFixed(2)).toLocaleString("ru-RU");
        status.textContent = `${dividend} ÷ ${currentDivisor} = ${displayedQuotient}`;
        render();
        return;
      }

      const wholeSteps = Math.floor(Math.abs(dividend) / currentDivisor);
      const step = dividend < 0 ? currentDivisor : -currentDivisor;
      point = dividend;
      for (let index = 0; index < wholeSteps; index += 1) {
        const nextPoint = point + step;
        jumps.push({ start: point, end: nextPoint });
        point = nextPoint;
      }
      status.textContent = `${dividend} ÷ ${currentDivisor} = ${wholeSteps}, остаток ${point}`;
      render();
    });
  }

  const multiplyButton = widget.querySelector("[data-multiply]");
  if (multiplyButton) {
    multiplyButton.addEventListener("click", () => {
      const multiplicand = widget.querySelector("[data-multiplicand]").valueAsNumber;
      const repetitions = widget.querySelector("[data-repetitions]").valueAsNumber;
      if (!Number.isInteger(multiplicand) || !Number.isInteger(repetitions)
        || Math.abs(multiplicand) > 10 || Math.abs(repetitions) > 10) {
        status.textContent = "Введите целые множители от −10 до 10.";
        return;
      }

      const count = Math.abs(repetitions);
      const addend = repetitions < 0 ? -multiplicand : multiplicand;
      const result = addend * count;
      point = initialPoint;
      jumps = [];
      if (result < minimum || result > maximum) {
        render();
        status.textContent = `Результат ${result} за пределами этой прямой (${minimum}…${maximum}).`;
        return;
      }

      for (let index = 0; index < count; index += 1) {
        const nextPoint = point + addend;
        jumps.push({ start: point, end: nextPoint });
        point = nextPoint;
      }

      const signedMultiplicand = multiplicand < 0 ? `(${multiplicand})` : multiplicand;
      const signedRepetitions = repetitions < 0 ? `(${repetitions})` : repetitions;
      const sum = jumps.map((jump) => (
        jump.end - jump.start < 0 ? `(${jump.end - jump.start})` : jump.end - jump.start
      )).join(" + ");
      status.textContent = `${signedMultiplicand} × ${signedRepetitions} = ${sum || "0"} = ${point}`;
      render();
    });
  }

  widget.querySelector("[data-reset]").addEventListener("click", () => {
    point = initialPoint;
    if (pointInput) pointInput.value = String(point);
    if (dividendInput) dividendInput.value = String(initialPoint);
    if (divisorInput) divisorInput.value = String(divisor);
    jumps = [];
    status.textContent = "";
    render();
  });
  (image.closest("p") || image).insertAdjacentElement("afterend", widgetRow);
  render();
}

document.querySelectorAll(".course-step-content img").forEach((image) => {
  image.classList.add("img-fluid");
});
document.querySelectorAll(".course-step-content table").forEach((table) => {
  table.classList.add("table", "table-bordered", "align-middle");
});
document.querySelectorAll(".course-step-content img[name]").forEach(addNumberLine);
