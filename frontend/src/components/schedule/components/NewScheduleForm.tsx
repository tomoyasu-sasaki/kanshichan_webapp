import { AddIcon, EditIcon } from '@chakra-ui/icons'
import { Button, Card, CardBody, CardHeader, FormControl, FormLabel, HStack, Heading, Icon, Input, VStack, Skeleton } from '@chakra-ui/react'
import { FaClock, FaPlus } from 'react-icons/fa'

interface NewScheduleFormProps {
  time: string
  content: string
  isLoading: boolean
  onChangeTime: (value: string) => void
  onChangeContent: (value: string) => void
  onSubmit: () => void
  onClear: () => void
}

export const NewScheduleForm: React.FC<NewScheduleFormProps> = ({ time, content, isLoading, onChangeTime, onChangeContent, onSubmit, onClear }) => {
  return (
    <Card shadow="lg">
      <CardHeader pb={2}>
        <HStack spacing={3}>
          <Icon as={FaPlus} color="green.500" boxSize={5} />
          <Heading size="md">新しい予定を追加</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        {isLoading ? (
          <>
            <Skeleton h="40px" mb={4} />
            <Skeleton h="40px" mb={4} />
            <Skeleton h="40px" />
          </>
        ) : (
          <VStack spacing={4} align="stretch">
            <VStack spacing={4} align="stretch">
              <FormControl id="time" isRequired>
                <FormLabel fontWeight="semibold">
                  <HStack spacing={2}>
                    <Icon as={FaClock} boxSize={4} />
                    時間
                  </HStack>
                </FormLabel>
                <Input type="time" value={time} onChange={(e) => onChangeTime(e.target.value)} isDisabled={isLoading} size="lg" borderRadius="lg" />
              </FormControl>
              <FormControl id="content" isRequired>
                <FormLabel fontWeight="semibold">
                  <HStack spacing={2}>
                    <Icon as={EditIcon} boxSize={4} />
                    内容
                  </HStack>
                </FormLabel>
                <Input type="text" placeholder="予定の内容を入力してください" value={content} onChange={(e) => onChangeContent(e.target.value)} isDisabled={isLoading} size="lg" borderRadius="lg" />
              </FormControl>
            </VStack>
            <HStack spacing={3} justify="flex-end">
              <Button variant="ghost" onClick={onClear} isDisabled={isLoading} borderRadius="lg">クリア</Button>
              <Button leftIcon={<AddIcon />} colorScheme="blue" onClick={onSubmit} isLoading={isLoading} size="lg" borderRadius="lg" px={8}>予定を追加</Button>
            </HStack>
          </VStack>
        )}
      </CardBody>
    </Card>
  )
}


