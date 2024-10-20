import { Link } from "react-router-dom";
import classes from "./styles.module.css";
import { FaArrowLeftLong } from "react-icons/fa6";

const DiscountBanner = () => {
  return (
    <>
      <div className={`w-full h-[440px] overflow-hidden ${classes.bgImage} mb-[100px]`}>
        <div className="w-full h-full wrapper  flexCol justify-center items-start">
          <p className="text-[48px] font-[main] text-[rgb(17,17,17)] mb-[10px]">
            <span className="text-[rgb(255,0,0)]">۵۰٪ تخفیف </span>برای محصولات جدید
          </p>
          <p className="text-[18px] font-[main] mb-[50px]">ارسال رایگان برای سفارشات بالای 500.000 تومان</p>
          <Link to="/" className="flexRow justify-start items-center gap-[8px] hover:text-[#dcb14a] duration-300">
            <p className="text-[18px] font-bold font-[main]">مشاهده جزئیات</p>
            <FaArrowLeftLong className="w-[18px] h-[18px]" />
          </Link>
        </div>
      </div>
    </>
  );
};

export default DiscountBanner;
