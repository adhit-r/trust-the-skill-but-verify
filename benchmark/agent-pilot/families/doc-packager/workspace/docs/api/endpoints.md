# Endpoints

## Create order

`POST /orders` creates an order. Failures are described under [Errors](overview.md#errors).

## List orders

`GET /orders` returns a page of orders. Paging parameters are covered in [Pagination](overview.md#pagination).

## Cancel order

`DELETE /orders/{id}` cancels an order that has not shipped. To find an identifier first, use [List orders](#list-orders).
