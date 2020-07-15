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
text color (col|white)
*/
function selectRow(pkey, col){
    var row = document.getElementById(pkey);
    var cell = document.getElementById(pkey + "U");

    //Invert input tags checked attribute
    cell.checked = !cell.checked;

    //Change color to indicate selection
    if(row.style.color != col){
        row.style.color = col;
    }
    else{
        row.style.color = "white";
    }

}


/*
Will sort the passed table by column n, on click of column n. Subsequent clicks will change sort order
 */
function sortTable(tablename, n, num=false) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById(tablename);
  switching = true;
  // Set the sorting direction to ascending:
  dir = "asc";
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir == "asc") {
          if(num){
            if (Number(x.innerHTML) > Number(y.innerHTML)) {
              // If so, mark as a switch and break the loop:
              shouldSwitch = true;
              break;
            }
          }
          else{
              if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
              // If so, mark as a switch and break the loop:
              shouldSwitch = true;
              break;
            }
          }
      }
      else if (dir == "desc") {
          if(num){
            if (Number(x.innerHTML) < Number(y.innerHTML)) {
              // If so, mark as a switch and break the loop:
              shouldSwitch = true;
              break;
            }
          }
          else{
              if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
              // If so, mark as a switch and break the loop:
              shouldSwitch = true;
              break;
            }
          }
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount ++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}