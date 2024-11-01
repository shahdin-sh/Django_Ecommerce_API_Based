import AddToCart from "../../../Components/AddToCart/AddToCart";
import QuantityInput from "../../../Components/QuantityInput/QuantityInput";

const SubmitHandler = ({ inventory, open, setOpen, productData, quantity, setQuantity, price }) => {
  let x = parseFloat(price).toFixed(2);
  const totalPrice = x * quantity;
  return (
    <>
      <div className="flexRow justify-start items-stretch gap-[15px]">
        <QuantityInput inventory={inventory} quantity={quantity} setQuantity={setQuantity} />
        <AddToCart open={open} setOpen={setOpen} productData={productData} quantity={quantity} setQuantity={setQuantity} price={totalPrice} />
      </div>
    </>
  );
};

export default SubmitHandler;
