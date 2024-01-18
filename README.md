## install
easy installation using Make
```
cp env.template .env
make start
```

## API

### Upsert
```
POST http://localhost:3001/api/upsert
Content-Type: application/json
Authorization: Bearer {{Authorization}}

{
  "content": "Guido Van Rossum, a computer programmer in the Netherlands, created Python.",
  username": "Proton"
}
```

### Asking
```
POST http://localhost:3001/api/asking
Content-Type: application/json
Authorization: Bearer {{Authorization}}

{
  "q": "Who created Python and in which year?",
  "username": "Proton"
}
```

### Million show
```
POST http://localhost:3001/api/million-show
Content-Type: application/json
Authorization: Bearer {{Authorization}}

{
  "theme": "Year Python was created",
  "amount": 100
}
```