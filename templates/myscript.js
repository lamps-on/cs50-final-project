$(document).ready(function(){
    $("#myForm").submit(function(){

        var search = $("$books").val);
        if (search == "")
        {
            alert("Enter the title of the book you are willing to give away");
        }

        else{
            var url = '';
            var img = '';
            var title = '';
            var author = '';

            $.get("https://www.google.apis.com/books/v1/volumes?q=" + search, function(response){

                for(i=0; i<response.items.length;i++)
                {
                    // get title of book
                    title = $('')
                }

            })
        }
    }
})