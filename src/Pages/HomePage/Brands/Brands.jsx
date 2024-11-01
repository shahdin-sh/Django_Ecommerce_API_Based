// Import Swiper React components
import { Swiper, SwiperSlide } from "swiper/react";

// Import Swiper styles
import "swiper/css";
import "swiper/css/navigation";

import "./styles.css";

// import required modules
import { Navigation } from "swiper/modules";

import brand from "../../../../public/images/brands/partner3.webp";
import { Link } from "react-router-dom";

const Brands = () => {
  return (
    <>
      <Swiper slidesPerView={5} spaceBetween={30} loop={true} navigation={true} modules={[Navigation]} className="Brands wrapper !mb-[480px] !py-[120px]">
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
        <SwiperSlide>
          <Link to="/">
            <img src={brand} alt="" />
          </Link>
        </SwiperSlide>
      </Swiper>
    </>
  );
};

export default Brands;
