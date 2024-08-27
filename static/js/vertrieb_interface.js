window.onload = function () {
    initializeInterface();
};

function initializeInterface() {
    hideWallboxTabInitially();
    registerWallboxCheckboxListener();
    registerTabClickListener();
    registerModuleChangeListener();
}

function hideWallboxTabInitially() {
    const wallboxTab = document.getElementById('wallbox-tab');
    if (wallboxTab) wallboxTab.style.display = 'none';
}

function registerWallboxCheckboxListener() {
    const wallboxCheckbox = document.getElementById('wallbox-checkbox');
    if (wallboxCheckbox) {
        wallboxCheckbox.addEventListener('change', toggleWallboxTabVisibility);
    }
}

function toggleWallboxTabVisibility() {
    const wallboxTab = document.getElementById('wallbox-tab');
    if (wallboxTab) {
        wallboxTab.style.display = this.checked ? 'block' : 'none';
    }
}

function registerTabClickListener() {
    const tabItems = document.querySelectorAll('.tab-item');
    tabItems.forEach((item) => {
        item.addEventListener('click', handleTabClick);
    });
}

function handleTabClick(event) {
    deactivateTabs();
    activateTab(event.target);
    hideTabContents();
    showTabContent(event.target);
}

function deactivateTabs() {
    const tabItems = document.querySelectorAll('.tab-item');
    tabItems.forEach((item) => {
        item.classList.remove('active');
    });
}

function activateTab(tab) {
    tab.classList.add('active');
}

function hideTabContents() {
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach((item) => {
        item.style.display = 'none';
    });
}

function showTabContent(tab) {
    const tabContentId = tab.getAttribute('data-tab');
    const tabContent = document.getElementById(tabContentId);
    if (tabContent) {
        tabContent.style.display = 'block';
    }
}

function registerModuleChangeListener() {
    const arbeitspreisField = document.getElementById('arbeitspreis');
    const verbrauchField = document.getElementById('verbrauch');
    const prognoseField = document.getElementById('prognose');
    const moduleNumber = document.getElementById('modulanzahl');
    const grundpreisField = document.getElementById('grundpreis');
    const zeitraumField = document.getElementById('zeitraum');
    const ausrichtungField = document.getElementById('ausrichtung');
    const komplexField = document.getElementById('komplex');

    if (ausrichtungField) ausrichtungField.addEventListener('change', handleFieldChange);
    if (komplexField) komplexField.addEventListener('change', handleFieldChange);
    if (arbeitspreisField) arbeitspreisField.addEventListener('change', handleFieldChange);
    if (verbrauchField) verbrauchField.addEventListener('change', handleFieldChange);
    if (prognoseField) prognoseField.addEventListener('change', handleFieldChange);
    if (moduleNumber) moduleNumber.addEventListener('change', handleModuleChange);
    if (grundpreisField) grundpreisField.addEventListener('change', handleZeitraumGrundpreisChange);
    if (zeitraumField) zeitraumField.addEventListener('change', handleZeitraumGrundpreisChange);
}

function handleZeitraumGrundpreisChange() {
    const zeitRaumElement = document.getElementById('zeitraum');
    const grundPreisElement = document.getElementById('grundpreis');

    let zeitRaum = zeitRaumElement instanceof HTMLInputElement ? parseInt(zeitRaumElement.value) : parseInt(zeitRaumElement.textContent);
    let grundPreis = grundPreisElement instanceof HTMLInputElement ? parseFloat(grundPreisElement.value) : parseFloat(grundPreisElement.textContent);

    if (isNaN(zeitRaum) || isNaN(grundPreis)) {
        console.error('Invalid input for zeitraum or grundpreis');
        return;
    }

    updateStrompreisGesamtSum(zeitRaum, grundPreis);
}

function handleFieldChange() {
    const arbeitspreisField = document.getElementById('arbeitspreis');
    const verbrauchField = document.getElementById('verbrauch');
    const prognoseField = document.getElementById('prognose');
    const zeitraumField = document.getElementById('zeitraum');
    const ausrichtungField = document.getElementById('ausrichtung');
    const komplexField = document.getElementById('komplex');

    let arbeitspreis = parseFloat(arbeitspreisField.value);
    let verbrauch = parseFloat(verbrauchField.value);
    let prognose = parseFloat(prognoseField.value);
    let zeitraum = parseInt(zeitraumField.value);
    let ausrichtung = ausrichtungField.value;
    let komplex = komplexField.value;

    if (isNaN(arbeitspreis) || isNaN(verbrauch) || isNaN(prognose) || isNaN(zeitraum)) {
        console.error('Invalid input for one or more fields');
        return;
    }

    updateArbeitspreisGesamt(arbeitspreis, verbrauch, prognose, zeitraum);
}


function handleModuleChange() {
    const modulePower = parseInt(document.getElementById('modulleistungWp').textContent);
    const moduleCount = parseInt(this.value);

    if (isNaN(modulePower) || isNaN(moduleCount)) {
        console.error('Invalid input for module_leistungWp or module_anzahl');
        return;
    }

    updateModuleSum(modulePower, moduleCount);
}

function updateModuleSum(modulePower, moduleCount) {
    const moduleSum = (modulePower / 1000) * moduleCount;
    const modulSumElem = document.getElementById('modulsumme_kWp');
    if (modulSumElem) {
        modulSumElem.textContent = moduleSum.toFixed(2);
    }
}

function updateStrompreisGesamtSum(zeitRaum, grundPreis) {
    const grundPreisGesamtSum = (grundPreis * 12 * zeitRaum);
    const stromGrundpreisGesamtElem = document.getElementById('stromgrundpreis_gesamt');
    if (stromGrundpreisGesamtElem) {
        stromGrundpreisGesamtElem.textContent = grundPreisGesamtSum.toFixed(2);
    }
}

function priceInflation(pricePerYear, increasePerYear, years) {
    let sumPrice = 0;
    let priceList = [];
    for (let i = 0; i < years; i++) {
        sumPrice += pricePerYear;
        priceList.push(sumPrice);
        pricePerYear = pricePerYear * (1.0 + increasePerYear);
    }
    return { sumPrice, priceList };
}

function arbeitspreis_gesamt(arbeitspreis, verbrauch, prognose, zeitraum) {
    let { sumPrice } = priceInflation(
        parseFloat(arbeitspreis) / 100 * parseFloat(verbrauch),
        parseFloat(prognose) / 100,
        zeitraum
    );
    return parseFloat(sumPrice.toFixed(2));
}

function arbeits_liste(arbeitspreis, verbrauch, prognose, zeitraum) {
    let { priceList } = priceInflation(
        parseFloat(arbeitspreis) / 100 * parseFloat(verbrauch),
        parseFloat(prognose) / 100,
        zeitraum
    );
    return priceList;
}

function erzProJahr(ausrichtung, andereKonfigurationsWerte) {
    let val = 0.00;
    if (ausrichtung === "Süd") {
        return andereKonfigurationsWerte["erzeugung_sued"];
    }
    if (ausrichtung === "Ost/West") {
        return andereKonfigurationsWerte["erzeugung_ost_west"];
    }
    return val;
}

function get_komplexity(komplex, andereKonfigurationWerte) {
    return parseFloat(andereKonfigurationWerte[komplex]);
}

document.addEventListener('DOMContentLoaded', registerFieldChangeListeners);