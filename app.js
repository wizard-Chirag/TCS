const exp = require('express')
const path = require('path')
const app = exp()

require('dotenv').config();

app.use(exp.urlencoded({extended:true}))
app.use(exp.json())

app.get('/',(req,res)=>{
    res.send("This is working!")
})

app.set('view engine','ejs')
app.listen(3690,()=>{
    console.log("Server is running on port 3000")
})