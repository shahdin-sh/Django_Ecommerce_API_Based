import { Link } from "react-router-dom";
import chairs from "../../../../public/images/category/chairs.jpg";
import tables from "../../../../public/images/category/tables.jpg";

const CategoryBanner = () => {
  return (
    <>
      <div className="w-full wrapper flexRow justify-center items-center !mt-[-180px] !mb-[100px] z-[3] !overflow-visible">
        <div className="w-fit h-fit flexRow p-[20px] gap-[20px] justify-center items-center bg-white z-[3]">
          <Link to="/" className="group overflow-hidden relative">
          <div className="w-full h-full absolute right-0 top-0 z-[3] flexRow justify-start items-center">
              <div className="h-full flexCol justify-start items-start py-[60px] px-[40px]">
                <p className="text-[30px] font-[main] text-[rgb(17,17,17)] group-hover:text-[#dcb14a] duration-500 mb-[10px]">مجموعه میز</p>
                <p className="text-[18px] font-[main] text-[rgb(17,17,17)]">مبلمان هلن</p>
              </div>
            </div>
            <img src={tables} alt="" className="object-cover group-hover:scale-[1.05] duration-500" />
          </Link>
          <Link to="/" className="group overflow-hidden relative">
            <div className="w-full h-full absolute right-0 top-0 z-[3] flexRow justify-start items-center">
              <div className="h-full flexCol justify-start items-start py-[60px] px-[40px]">
                <p className="text-[30px] font-[main] text-[rgb(17,17,17)] group-hover:text-[#dcb14a] duration-500 mb-[10px]">مجموعه صندلی</p>
                <p className="text-[18px] font-[main] text-[rgb(17,17,17)]">مبلمان هلن</p>
              </div>
            </div>
            <img src={chairs} alt="" className="object-cover group-hover:scale-[1.05] duration-500" />
          </Link>
        </div>
      </div>
    </>
  );
};

export default CategoryBanner;
