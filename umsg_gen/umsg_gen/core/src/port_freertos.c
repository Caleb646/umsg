//
// Created by alexp on 9/6/2022.
//
#include <umsg.h>
#include <FreeRTOS.h>
#include <queue.h>
#include <stdint.h>


bool is_isr_active()
{
    return xPortIsInsideInterrupt() == pdTRUE;
}

void * umsg_port_malloc(uint32_t size)
{
    return pvPortMalloc(size);
}

umsg_sub_handle_t umsg_port_create(uint32_t size, uint8_t length)
{
    return xQueueCreate(length, size);
}

void umsg_port_send(umsg_sub_t* sub, void * data)
{
    QueueHandle_t queue = (QueueHandle_t)sub->sub_handle;
    if(sub->length > 1)
    {
        if(is_isr_active())
        {
            BaseType_t xHigherPriorityTaskWoken;
            xQueueSendToBackFromISR(queue, data,
                                    &xHigherPriorityTaskWoken);
            portYIELD_FROM_ISR(xHigherPriorityTaskWoken);

        }
        else
        {
            xQueueSendToBack(queue, data, 0);
        }
    }
    else
    {
        // check if in interrupt context
        if(is_isr_active())
        {
            BaseType_t xHigherPriorityTaskWoken;
            xQueueOverwriteFromISR(queue, data,
                                   &xHigherPriorityTaskWoken);
            portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
        }
        else
        {
            xQueueOverwrite(queue, data);
        }
    }
}

uint8_t umsg_port_receive(umsg_sub_handle_t sub_handle, void * data, uint32_t timeout)
{
    return xQueueReceive((QueueHandle_t)sub_handle, data, timeout);
}