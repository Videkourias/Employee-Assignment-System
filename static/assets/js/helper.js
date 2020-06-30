//Helper file containing various JS functions that template pages use

/*
Name: newEmployee
Input/Output: Takes a string called value as input, value corresponds to the value of the option selected
       from the selection dropdown on the form.
Purpose: Function called to display or hide elements based on what user type is being created
       ie. Selecting a user type(value) of 1 will hide the assignedto field
*/
    function newEmployee(value){
        if (value == 1){
            document.getElementById("assignedto").style.display="none";
        }
        else{
            document.getElementById("assignedto").style.display="block";
        }
    }