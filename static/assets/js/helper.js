//Helper file containing various JS functions that template pages use

/*
Takes in the userType value currently selected and hides the
entire div containing Assignment if userType == 1 (admin)
*/
function newEmployee(value){
    if (value == 1){
        document.getElementById("assignedto").style.display="none";
    }
    else{
        document.getElementById("assignedto").style.display="block";
    }
}

/*
Will invert the display style of the submit button based on the state of a checkbox (none|initial)
*/
function displaySubmit(boxID, submitID){
    var box = document.getElementById(boxID);
    var submit = document.getElementById(submitID);
    if (box.checked){
        submit.style.display = "initial";
    }
    else{
        submit.style.display = "none";
    }
}
/*
Will invert the checked attribute of the checkbox cell in the row, and also flip the rows
text color (red|white)
*/
function selectRow(pkey){
    var row = document.getElementById(pkey);
    var cell = document.getElementById(pkey + "U");

    //Invert input tags checked attribute
    cell.checked = !cell.checked;

    //Change color to indicate selection
    if(row.style.color != "red"){
        row.style.color = "red";
    }
    else{
        row.style.color = "white";
    }

}