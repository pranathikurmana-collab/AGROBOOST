let productions = JSON.parse(localStorage.getItem("productions")) || [];

// Add Production
let productionForm = document.getElementById("productionForm");

if(productionForm){

productionForm.addEventListener("submit", function(e){

e.preventDefault();

let farmer = document.getElementById("farmer").value;
let crop = document.getElementById("crop").value;
let quantity = parseInt(document.getElementById("quantity").value);

let bonus = 0;

if(quantity > 1000){
bonus = 5000;
}
else if(quantity >= 500){
bonus = 2000;
}

productions.push({farmer,crop,quantity,bonus});

localStorage.setItem("productions", JSON.stringify(productions));

alert("Production Added!");

productionForm.reset();

});

}

// Display Table
let table = document.getElementById("productionTable");

if(table){

productions.forEach(p => {

let row = table.insertRow();

row.insertCell(0).innerText = p.farmer;
row.insertCell(1).innerText = p.crop;
row.insertCell(2).innerText = p.quantity;
row.insertCell(3).innerText = "₹" + p.bonus;

});

}