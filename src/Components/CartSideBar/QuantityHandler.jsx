import { useRef, useState } from "react";

const QuantityHandler = ({ realQuantity }) => {
  const [quantity, setQuantitiy] = useState(realQuantity);
  const ref = useRef();

  const incHandler = () => {
    setQuantitiy(quantity + 1);
  };

  const decHandler = () => {
    setQuantitiy(quantity - 1);
  };

  return (
    <>
      <div className="w-[60px] self-stretch flexRow items-center justify-center">
        <button onClick={incHandler} className="w-[20px]">
          +
        </button>
        <p className="text-[12px] font-[main]">{quantity}</p>
        <button onClick={decHandler} className="w-[20px]">
          -
        </button>
      </div>
    </>
  );
};

export default QuantityHandler;
